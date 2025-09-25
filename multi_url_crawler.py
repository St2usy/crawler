import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
from datetime import datetime
import concurrent.futures
from threading import Lock
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MultiURLCrawler:
    def __init__(self):
        """
        다중 URL 크롤링을 위한 클래스 초기화
        """
        self.base_url = 'https://csai.jbnu.ac.kr'
        self.data_lock = Lock()
        
        # 크롤링할 URL들과 카테고리 정보
        self.target_urls = {
            'https://csai.jbnu.ac.kr/csai/29105/subview.do': '학과소식',
            'https://csai.jbnu.ac.kr/csai/29106/subview.do': '일반공지',
            'https://csai.jbnu.ac.kr/csai/29107/subview.do': '학사공지',
            'https://csai.jbnu.ac.kr/csai/31501/subview.do': '사업단공지',
            'https://csai.jbnu.ac.kr/csai/29108/subview.do': '취업정보'
        }
        
        self.all_data = []
        logging.info(f"다중 URL 크롤러 초기화 완료 - {len(self.target_urls)}개 URL")

    def get_total_pages(self, soup):
        """
        총 페이지 수 가져오기
        """
        paging_div = soup.find('div', class_='_paging')
        if paging_div:
            total_page_span = paging_div.find('span', class_='_totPage')
            if total_page_span:
                return int(re.search(r'\d+', total_page_span.text).group())
        return 1

    def parse_page(self, html, category):
        """
        페이지 파싱하여 게시글 데이터 추출
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = []
        
        table = soup.find('table', class_='artclTable')
        if not table:
            logging.warning(f"[{category}] 공지사항 테이블을 찾을 수 없습니다.")
            return []
        
        rows = table.find('tbody').find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 6:
                continue
                
            number = cols[0].text.strip()
            
            # 제목과 링크 추출
            title_cell = cols[1]
            title_link = title_cell.find('a')
            if title_link:
                title = title_link.get_text()
                title = ' '.join(title.split())
                href = title_link.get('href', '')
                full_url = urljoin(self.base_url, href) if href else ''
            else:
                title = title_cell.get_text()
                title = ' '.join(title.split())
                full_url = ''
            
            author = cols[2].text.strip()
            date = cols[3].text.strip()
            attachments = cols[4].text.strip()
            views = cols[5].text.strip()
            
            post_data = {
                'category': category,
                'number': number,
                'title': title,
                'author': author,
                'date': date,
                'attachments': attachments,
                'views': views,
                'url': full_url,
                'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data.append(post_data)
        
        return data

    def get_post_content(self, url):
        """
        게시글 상세 내용 가져오기
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_text = ''
            
            # artclView div에서 내용 추출
            artcl_view = soup.find('div', class_='artclView')
            if artcl_view:
                content_text = artcl_view.get_text()
                content_text = ' '.join(content_text.split())
                lines = content_text.split()
                if len(lines) > 10:
                    content_text = ' '.join(lines[5:])
            
            # hwp_editor_board_content div에서 내용 추출
            if not content_text:
                hwp_content = soup.find('div', class_='hwp_editor_board_content')
                if hwp_content:
                    content_text = hwp_content.get_text()
                    content_text = ' '.join(content_text.split())
            
            return content_text
            
        except Exception as e:
            logging.error(f"상세 내용 가져오기 실패 ({url}): {e}")
            return ''

    def crawl_single_url(self, url, category, max_pages=2):
        """
        단일 URL 크롤링
        """
        logging.info(f"[{category}] 크롤링 시작: {url}")
        url_data = []
        
        try:
            # 첫 페이지에서 총 페이지 수 확인
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            total_pages = min(self.get_total_pages(soup), max_pages)
            
            logging.info(f"[{category}] 총 {total_pages}페이지 크롤링 예정")
            
            for page_num in range(1, total_pages + 1):
                params = {'page': page_num}
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    page_data = self.parse_page(response.text, category)
                    
                    # 상세 내용 가져오기
                    for post in page_data:
                        if post['url']:
                            content = self.get_post_content(post['url'])
                            post['content'] = content
                            time.sleep(0.3)  # 서버 부하 방지
                    
                    url_data.extend(page_data)
                    logging.info(f"[{category}] 페이지 {page_num}/{total_pages} 완료: {len(page_data)}개 게시글")
                    time.sleep(0.5)  # 페이지 간 딜레이
                    
                except Exception as e:
                    logging.error(f"[{category}] 페이지 {page_num} 크롤링 실패: {e}")
                    continue
            
            logging.info(f"[{category}] 크롤링 완료: 총 {len(url_data)}개 게시글")
            
        except Exception as e:
            logging.error(f"[{category}] 크롤링 중 오류 발생: {e}")
        
        return url_data

    def crawl_all_urls(self, max_pages=2, use_threading=True):
        """
        모든 URL을 크롤링
        """
        logging.info("다중 URL 크롤링 시작...")
        start_time = time.time()
        
        if use_threading:
            # 병렬 처리로 크롤링
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # 각 URL에 대해 크롤링 작업 제출
                future_to_url = {
                    executor.submit(self.crawl_single_url, url, category, max_pages): (url, category)
                    for url, category in self.target_urls.items()
                }
                
                # 결과 수집
                for future in concurrent.futures.as_completed(future_to_url):
                    url, category = future_to_url[future]
                    try:
                        url_data = future.result()
                        with self.data_lock:
                            self.all_data.extend(url_data)
                        logging.info(f"[{category}] {len(url_data)}개 게시글 수집 완료")
                    except Exception as e:
                        logging.error(f"[{category}] 크롤링 실패: {e}")
        else:
            # 순차 처리로 크롤링
            for url, category in self.target_urls.items():
                url_data = self.crawl_single_url(url, category, max_pages)
                self.all_data.extend(url_data)
        
        end_time = time.time()
        logging.info(f"전체 크롤링 완료: {len(self.all_data)}개 게시글, 소요시간: {end_time - start_time:.2f}초")
        
        return self.all_data

    def save_to_json(self, filename=None):
        """
        데이터를 JSON 파일로 저장
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_notices_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=2)
            logging.info(f"JSON 파일 저장 완료: {filename}")
            return filename
        except Exception as e:
            logging.error(f"JSON 파일 저장 실패: {e}")
            return None

    def get_summary_by_category(self):
        """
        카테고리별 요약 정보 반환
        """
        summary = {}
        for post in self.all_data:
            category = post.get('category', 'Unknown')
            if category not in summary:
                summary[category] = 0
            summary[category] += 1
        return summary

    def print_summary(self):
        """
        크롤링 결과 요약 출력
        """
        print(f"\n=== 크롤링 결과 요약 ===")
        print(f"총 게시글 수: {len(self.all_data)}개")
        
        summary = self.get_summary_by_category()
        for category, count in summary.items():
            print(f"- {category}: {count}개")
        
        print(f"\n=== 최신 게시글 (각 카테고리별 3개씩) ===")
        for category in self.target_urls.values():
            category_posts = [post for post in self.all_data if post.get('category') == category]
            category_posts = sorted(category_posts, key=lambda x: x.get('date', ''), reverse=True)[:3]
            
            print(f"\n[{category}]")
            for i, post in enumerate(category_posts, 1):
                print(f"  {i}. [{post.get('date', 'N/A')}] {post.get('title', 'N/A')[:60]}...")

def main():
    """
    메인 함수
    """
    print("전북대학교 컴퓨터인공지능학부 다중 URL 크롤링을 시작합니다...")
    print("크롤링 대상:")
    for url, category in {
        'https://csai.jbnu.ac.kr/csai/29105/subview.do': '학과소식',
        'https://csai.jbnu.ac.kr/csai/29106/subview.do': '일반공지',
        'https://csai.jbnu.ac.kr/csai/29107/subview.do': '학사공지',
        'https://csai.jbnu.ac.kr/csai/31501/subview.do': '사업단공지',
        'https://csai.jbnu.ac.kr/csai/29108/subview.do': '취업정보'
    }.items():
        print(f"  - {category}: {url}")
    
    crawler = MultiURLCrawler()
    
    # 크롤링 실행 (병렬 처리 사용)
    all_data = crawler.crawl_all_urls(max_pages=2, use_threading=True)
    
    if all_data:
        # JSON 파일로 저장
        filename = crawler.save_to_json()
        
        # 요약 정보 출력
        crawler.print_summary()
        
        print(f"\n크롤링 완료! 데이터가 {filename}에 저장되었습니다.")
    else:
        print("\n수집할 데이터가 없습니다. 크롤링 과정에서 문제가 발생했을 수 있습니다.")

if __name__ == "__main__":
    main()
