import requests
from bs4 import BeautifulSoup
import json
import time
import schedule
from datetime import datetime
from urllib.parse import urljoin
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ScheduledCrawler:
    def __init__(self, config_file='crawler_config.json'):
        """
        주기적 크롤링을 위한 클래스 초기화
        """
        self.config = self.load_config(config_file)
        self.base_url = self.config.get('base_url', 'https://csai.jbnu.ac.kr')
        self.target_url = self.config.get('target_url', 'https://csai.jbnu.ac.kr/csai/29107/subview.do')
        self.data_file = self.config.get('data_file', 'notices_data.json')
        self.check_interval = self.config.get('check_interval_minutes', 30)  # 기본 30분마다 체크
        self.max_pages = self.config.get('max_pages', 2)
        
        # 기존 데이터 로드
        self.existing_data = self.load_existing_data()
        
        logging.info(f"스케줄러 초기화 완료 - 체크 간격: {self.check_interval}분, 데이터 파일: {self.data_file}")

    def load_config(self, config_file):
        """
        설정 파일 로드
        """
        default_config = {
            "base_url": "https://csai.jbnu.ac.kr",
            "target_url": "https://csai.jbnu.ac.kr/csai/29107/subview.do",
            "data_file": "notices_data.json",
            "check_interval_minutes": 30,
            "max_pages": 2,
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "message_template": "새로운 공지사항이 등록되었습니다: {title}"
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
                import re
                return min(int(re.search(r'\d+', total_page_span.text).group()), self.max_pages)
        return 1

    def parse_page(self, html):
        """
        페이지 파싱하여 게시글 데이터 추출
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = []
        
        table = soup.find('table', class_='artclTable')
        if not table:
            logging.warning("공지사항 테이블을 찾을 수 없습니다.")
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

    def crawl_new_posts(self):
        """
        새로운 게시글 크롤링
        """
        logging.info("새로운 게시글 확인 시작...")
        
        try:
            # 첫 페이지에서 총 페이지 수 확인
            response = requests.get(self.target_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            total_pages = self.get_total_pages(soup)
            
            logging.info(f"총 {total_pages}페이지 확인 중...")
            
            all_new_posts = []
            existing_urls = {post.get('url', '') for post in self.existing_data}
            
            for page_num in range(1, total_pages + 1):
                params = {'page': page_num}
                
                try:
                    response = requests.get(self.target_url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    page_data = self.parse_page(response.text)
                    
                    for post in page_data:
                        # 새로운 게시글인지 확인 (URL 기준)
                        if post['url'] and post['url'] not in existing_urls:
                            logging.info(f"새 게시글 발견: {post['title'][:50]}...")
                            
                            # 상세 내용 가져오기
                            content = self.get_post_content(post['url'])
                            post['content'] = content
                            
                            all_new_posts.append(post)
                            existing_urls.add(post['url'])
                            
                            # 서버 부하 방지를 위한 딜레이
                            time.sleep(0.5)
                    
                    time.sleep(1)  # 페이지 간 딜레이
                    
                except Exception as e:
                    logging.error(f"페이지 {page_num} 크롤링 실패: {e}")
                    continue
            
            if all_new_posts:
                # 새로운 데이터를 기존 데이터 앞에 추가
                self.existing_data = all_new_posts + self.existing_data
                self.save_data()
                
                logging.info(f"새로운 게시글 {len(all_new_posts)}개 발견 및 저장 완료")
                
                # 알림 발송 (설정된 경우)
                if self.config.get('notification', {}).get('enabled'):
                    self.send_notifications(all_new_posts)
                
                return all_new_posts
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
        message_template = notification_config.get('message_template', "새로운 공지사항이 등록되었습니다: {title}")
        
        if webhook_url:
            for post in new_posts:
                message = message_template.format(title=post['title'])
                # 여기에 웹훅 발송 로직 추가 (Discord, Slack 등)
                logging.info(f"알림 발송: {message}")

    def start_scheduler(self):
        """
        스케줄러 시작
        """
        logging.info(f"스케줄러 시작 - {self.check_interval}분마다 실행")
        
        # 즉시 한 번 실행
        self.crawl_new_posts()
        
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

def main():
    """
    메인 함수
    """
    import sys
    
    crawler = ScheduledCrawler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 한 번만 실행
        new_posts = crawler.run_once()
        if new_posts:
            print(f"\n새로운 게시글 {len(new_posts)}개 발견:")
            for post in new_posts:
                print(f"- [{post['date']}] {post['title']}")
        else:
            print("새로운 게시글이 없습니다.")
    else:
        # 스케줄러 시작
        crawler.start_scheduler()

if __name__ == "__main__":
    main()
