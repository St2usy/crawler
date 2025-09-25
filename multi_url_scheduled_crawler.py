import requests
from bs4 import BeautifulSoup
import json
import time
import re
import schedule
from urllib.parse import urljoin
from datetime import datetime
import concurrent.futures
from threading import Lock
import logging
import os
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_scheduled_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MultiURLScheduledCrawler:
    def __init__(self, config_file='multi_crawler_config.json'):
        """
        다중 URL 스케줄러 크롤러 초기화
        """
        self.config = self.load_config(config_file)
        self.base_url = self.config.get('base_url', 'https://csai.jbnu.ac.kr')
        self.data_file = self.config.get('data_file', 'multi_notices_data.json')
        self.check_interval = self.config.get('check_interval_minutes', 30)
        self.max_pages = self.config.get('max_pages', 2)
        self.data_lock = Lock()
        
        # 크롤링할 URL들과 카테고리 정보
        self.target_urls = self.config.get('target_urls', {
            'https://csai.jbnu.ac.kr/csai/29105/subview.do': '학과소식',
            'https://csai.jbnu.ac.kr/csai/29106/subview.do': '일반공지',
            'https://csai.jbnu.ac.kr/csai/29107/subview.do': '학사공지',
            'https://csai.jbnu.ac.kr/csai/31501/subview.do': '사업단공지',
            'https://csai.jbnu.ac.kr/csai/29108/subview.do': '취업정보'
        })
        
        # 기존 데이터 로드
        self.existing_data = self.load_existing_data()
        
        logging.info(f"다중 URL 스케줄러 초기화 완료 - {len(self.target_urls)}개 URL, 체크 간격: {self.check_interval}분")

    def load_config(self, config_file):
        """
        설정 파일 로드
        """
        default_config = {
            "base_url": "https://csai.jbnu.ac.kr",
            "data_file": "multi_notices_data.json",
            "check_interval_minutes": 30,
            "max_pages": 2,
            "target_urls": {
                "https://csai.jbnu.ac.kr/csai/29105/subview.do": "학과소식",
                "https://csai.jbnu.ac.kr/csai/29106/subview.do": "일반공지",
                "https://csai.jbnu.ac.kr/csai/29107/subview.do": "학사공지",
                "https://csai.jbnu.ac.kr/csai/31501/subview.do": "사업단공지",
                "https://csai.jbnu.ac.kr/csai/29108/subview.do": "취업정보"
            },
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "message_template": "새로운 공지사항이 등록되었습니다: [{category}] {title}"
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 기본값과 병합
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        # 설정 파일이 없으면 기본 설정으로 생성
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logging.info(f"기본 설정 파일 생성: {config_file}")
        return default_config

    def load_existing_data(self):
        """
        기존 크롤링 데이터 로드
        """
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"기존 데이터 로드 완료: {len(data)}개 게시글")
                    return data
            except Exception as e:
                logging.error(f"기존 데이터 로드 실패: {e}")
        
        logging.info("기존 데이터 파일이 없습니다. 새로 시작합니다.")
        return []

    def get_total_pages(self, soup):
        """
        총 페이지 수 가져오기
        """
        paging_div = soup.find('div', class_='_paging')
        if paging_div:
            total_page_span = paging_div.find('span', class_='_totPage')
            if total_page_span:
                return min(int(re.search(r'\d+', total_page_span.text).group()), self.max_pages)
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
                'content': '',
                'content_html': '',
                'image_urls': [],
                'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data.append(post_data)
        
        return data

    def get_post_content(self, url):
        """
        게시글 상세 내용, HTML 원문, 이미지 URL들 가져오기
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_text = ''
            content_html = ''
            image_urls = []
            
            # artclView div에서 내용 추출
            artcl_view = soup.find('div', class_='artclView')
            if artcl_view:
                # HTML 원문 저장
                content_html = str(artcl_view)
                
                # 텍스트 내용 추출
                content_text = artcl_view.get_text()
                content_text = ' '.join(content_text.split())
                lines = content_text.split()
                if len(lines) > 10:
                    content_text = ' '.join(lines[5:])
                
                # 이미지 URL들 추출
                img_tags = artcl_view.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        # 상대 URL을 절대 URL로 변환
                        full_img_url = urljoin(self.base_url, src)
                        image_urls.append(full_img_url)
            
            # hwp_editor_board_content div에서 내용 추출
            if not content_text:
                hwp_content = soup.find('div', class_='hwp_editor_board_content')
                if hwp_content:
                    content_html = str(hwp_content)
                    content_text = hwp_content.get_text()
                    content_text = ' '.join(content_text.split())
                    
                    # 이미지 URL들 추출
                    img_tags = hwp_content.find_all('img')
                    for img in img_tags:
                        src = img.get('src')
                        if src:
                            full_img_url = urljoin(self.base_url, src)
                            image_urls.append(full_img_url)
            
            return {
                'content_text': content_text,
                'content_html': content_html,
                'image_urls': image_urls
            }
            
        except Exception as e:
            logging.error(f"상세 내용 가져오기 실패 ({url}): {e}")
            return {
                'content_text': '',
                'content_html': '',
                'image_urls': []
            }

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
            total_pages = self.get_total_pages(soup)
            
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
                            content_data = self.get_post_content(post['url'])
                            post['content'] = content_data['content_text']
                            post['content_html'] = content_data['content_html']
                            post['image_urls'] = content_data['image_urls']
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
        all_data = []
        
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
                        all_data.extend(url_data)
                        logging.info(f"[{category}] {len(url_data)}개 게시글 수집 완료")
                    except Exception as e:
                        logging.error(f"[{category}] 크롤링 실패: {e}")
        else:
            # 순차 처리로 크롤링
            for url, category in self.target_urls.items():
                url_data = self.crawl_single_url(url, category, max_pages)
                all_data.extend(url_data)
        
        end_time = time.time()
        logging.info(f"전체 크롤링 완료: {len(all_data)}개 게시글, 소요시간: {end_time - start_time:.2f}초")
        
        return all_data

    def find_new_posts(self, current_data):
        """
        새로운 게시글 찾기
        """
        # 기존 데이터의 URL 집합 생성
        existing_urls = {post.get('url', '') for post in self.existing_data if post.get('url')}
        
        new_posts = []
        for post in current_data:
            if post.get('url') and post['url'] not in existing_urls:
                new_posts.append(post)
                logging.info(f"새 게시글 발견: [{post.get('category', 'Unknown')}] {post.get('title', 'N/A')[:50]}...")
        
        return new_posts

    def crawl_new_posts(self):
        """
        새로운 게시글만 크롤링
        """
        logging.info("새로운 게시글 확인 시작...")
        
        try:
            # 모든 URL에서 최신 데이터 수집
            current_data = self.crawl_all_urls(max_pages=self.max_pages, use_threading=True)
            
            # 새로운 게시글 찾기
            new_posts = self.find_new_posts(current_data)
            
            if new_posts:
                # 새로운 데이터를 기존 데이터 앞에 추가
                with self.data_lock:
                    self.existing_data = new_posts + self.existing_data
                    self.save_data()
                
                logging.info(f"새로운 게시글 {len(new_posts)}개 발견 및 저장 완료")
                
                # 알림 발송 (설정된 경우)
                if self.config.get('notification', {}).get('enabled'):
                    self.send_notifications(new_posts)
                
                return new_posts
            else:
                logging.info("새로운 게시글이 없습니다.")
                return []
                
        except Exception as e:
            logging.error(f"크롤링 중 오류 발생: {e}")
            return []

    def save_data(self):
        """
        데이터를 JSON 파일로 저장
        """
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.existing_data, f, ensure_ascii=False, indent=2)
            logging.info(f"데이터 저장 완료: {self.data_file}")
        except Exception as e:
            logging.error(f"데이터 저장 실패: {e}")

    def send_notifications(self, new_posts):
        """
        새로운 게시글에 대한 알림 발송
        """
        notification_config = self.config.get('notification', {})
        if not notification_config.get('enabled'):
            return
        
        webhook_url = notification_config.get('webhook_url')
        message_template = notification_config.get('message_template', "새로운 공지사항이 등록되었습니다: [{category}] {title}")
        
        if webhook_url:
            for post in new_posts:
                message = message_template.format(
                    category=post.get('category', 'Unknown'),
                    title=post.get('title', 'N/A')
                )
                # 여기에 웹훅 발송 로직 추가 (Discord, Slack 등)
                logging.info(f"알림 발송: {message}")

    def get_summary_by_category(self):
        """
        카테고리별 요약 정보 반환
        """
        summary = {}
        for post in self.existing_data:
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
        print(f"총 게시글 수: {len(self.existing_data)}개")
        
        summary = self.get_summary_by_category()
        for category, count in summary.items():
            print(f"- {category}: {count}개")
        
        print(f"\n=== 최신 게시글 (각 카테고리별 3개씩) ===")
        for category in self.target_urls.values():
            category_posts = [post for post in self.existing_data if post.get('category') == category]
            category_posts = sorted(category_posts, key=lambda x: x.get('date', ''), reverse=True)[:3]
            
            print(f"\n[{category}]")
            for i, post in enumerate(category_posts, 1):
                image_count = len(post.get('image_urls', []))
                image_info = f" (이미지 {image_count}개)" if image_count > 0 else ""
                print(f"  {i}. [{post.get('date', 'N/A')}] {post.get('title', 'N/A')[:60]}...{image_info}")

    def start_scheduler(self):
        """
        스케줄러 시작
        """
        logging.info(f"다중 URL 스케줄러 시작 - {self.check_interval}분마다 실행")
        
        # 즉시 한 번 실행
        new_posts = self.crawl_new_posts()
        if new_posts:
            print(f"\n새로운 게시글 {len(new_posts)}개 발견:")
            for post in new_posts:
                print(f"- [{post.get('category', 'Unknown')}] [{post.get('date', 'N/A')}] {post.get('title', 'N/A')}")
        else:
            print("새로운 게시글이 없습니다.")
        
        # 주기적 실행 설정
        schedule.every(self.check_interval).minutes.do(self.crawl_new_posts)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 스케줄 체크
        except KeyboardInterrupt:
            logging.info("사용자에 의해 스케줄러가 중단되었습니다.")
        except Exception as e:
            logging.error(f"스케줄러 오류: {e}")

    def run_once(self):
        """
        한 번만 실행 (테스트용)
        """
        logging.info("한 번만 실행 모드")
        return self.crawl_new_posts()

    def run_full_crawl(self):
        """
        전체 크롤링 실행 (기존 데이터 무시)
        """
        logging.info("전체 크롤링 모드")
        all_data = self.crawl_all_urls(max_pages=self.max_pages, use_threading=True)
        
        with self.data_lock:
            self.existing_data = all_data
            self.save_data()
        
        logging.info(f"전체 크롤링 완료: {len(all_data)}개 게시글")
        return all_data

def main():
    """
    메인 함수
    """
    crawler = MultiURLScheduledCrawler()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # 한 번만 실행
            new_posts = crawler.run_once()
            if new_posts:
                print(f"\n새로운 게시글 {len(new_posts)}개 발견:")
                for post in new_posts:
                    print(f"- [{post.get('category', 'Unknown')}] [{post.get('date', 'N/A')}] {post.get('title', 'N/A')}")
            else:
                print("새로운 게시글이 없습니다.")
        elif sys.argv[1] == '--full':
            # 전체 크롤링
            all_data = crawler.run_full_crawl()
            crawler.print_summary()
        elif sys.argv[1] == '--summary':
            # 요약 정보만 출력
            crawler.print_summary()
        else:
            print("사용법:")
            print("  python multi_url_scheduled_crawler.py          # 스케줄러 시작")
            print("  python multi_url_scheduled_crawler.py --once   # 한 번만 실행")
            print("  python multi_url_scheduled_crawler.py --full   # 전체 크롤링")
            print("  python multi_url_scheduled_crawler.py --summary # 요약 정보 출력")
    else:
        # 스케줄러 시작
        crawler.start_scheduler()

if __name__ == "__main__":
    main()
