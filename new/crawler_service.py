import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from threading import Lock
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import schedule
from dotenv import load_dotenv

from models import NoticeResponse, CrawlStatus, CategorySummary
from firebase_service import FirebaseService
from scheduler_service import SchedulerService

# .env 파일 로드
load_dotenv()

class CrawlerService:
    def __init__(self, config_file='crawler_config.json'):
        """
        크롤러 서비스 초기화
        """
        self.config = self.load_config(config_file)
        self.base_url = self.config.get('base_url', 'https://csai.jbnu.ac.kr')
        self.data_file = self.config.get('data_file', 'notices_data.json')
        self.max_pages = self.config.get('max_pages', 2)
        self.data_lock = Lock()
        self.crawl_status = "idle"
        self.last_crawl_time = None
        
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
        
        # Firebase 서비스 초기화
        self.firebase_service = FirebaseService()
        
        # 스케줄러 서비스 초기화
        self.scheduler_service = SchedulerService()
        self.scheduler_service.set_crawl_callback(self.crawl_new_posts)
        
        # Firebase 동기화 활성화 여부 확인
        self.firebase_enabled = os.getenv('ENABLE_FIREBASE_SYNC', 'false').lower() == 'true'
        
        logging.info(f"크롤러 서비스 초기화 완료 - {len(self.target_urls)}개 URL")
        logging.info(f"Firebase 동기화: {'활성화' if self.firebase_enabled else '비활성화'}")
    
    def get_base_url(self, url):
        """URL에 따라 적절한 base_url 반환"""
        if 'swuniv.jbnu.ac.kr' in url:
            return 'https://swuniv.jbnu.ac.kr'
        elif 'csai.jbnu.ac.kr' in url:
            return 'https://csai.jbnu.ac.kr'
        else:
            return self.base_url

    def load_config(self, config_file):
        """설정 파일 로드"""
        default_config = {
            "base_url": "https://csai.jbnu.ac.kr",
            "data_file": "notices_data.json",
            "max_pages": 2,
            "target_urls": {
                "https://csai.jbnu.ac.kr/csai/29105/subview.do": "학과소식",
                "https://csai.jbnu.ac.kr/csai/29106/subview.do": "일반공지",
                "https://csai.jbnu.ac.kr/csai/29107/subview.do": "학사공지",
                "https://csai.jbnu.ac.kr/csai/31501/subview.do": "사업단공지",
                "https://csai.jbnu.ac.kr/csai/29108/subview.do": "취업정보"
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
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
        """기존 크롤링 데이터 로드"""
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

    def get_total_pages(self, soup, url=''):
        """총 페이지 수 가져오기"""
        # 기존 csai.jbnu.ac.kr 사이트 페이지네이션
        if 'csai.jbnu.ac.kr' in url or not url:
            paging_div = soup.find('div', class_='_paging')
            if paging_div:
                total_page_span = paging_div.find('span', class_='_totPage')
                if total_page_span:
                    return min(int(re.search(r'\d+', total_page_span.text).group()), self.max_pages)
        
        # 새로운 swuniv.jbnu.ac.kr 사이트 페이지네이션
        elif 'swuniv.jbnu.ac.kr' in url:
            # 프로그램 신청 페이지의 경우 숫자 링크에서 최대 페이지 찾기
            number_links = soup.find_all('a', href=True)
            page_numbers = []
            for link in number_links:
                text = link.get_text().strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            
            if page_numbers:
                max_page = max(page_numbers)
                return min(max_page, self.max_pages)
            
            # 다양한 페이지네이션 구조 시도
            paging_selectors = [
                'div.paging',
                'div.pagination',
                'div.page-navigation',
                'div.page-nav',
                'ul.pagination',
                'div.pager'
            ]
            
            for selector in paging_selectors:
                paging_div = soup.find('div', class_=selector) or soup.find('ul', class_=selector)
                if paging_div:
                    # 페이지 번호 링크들 찾기
                    page_links = paging_div.find_all('a', href=True)
                    if page_links:
                        max_page = 1
                        for link in page_links:
                            page_text = link.get_text().strip()
                            if page_text.isdigit():
                                max_page = max(max_page, int(page_text))
                        return min(max_page, self.max_pages)
            
            # 숫자 텍스트에서 페이지 수 찾기
            page_text = soup.get_text()
            page_match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
            if page_match:
                return min(int(page_match.group(2)), self.max_pages)
        
        return 1

    def parse_page(self, html, category):
        """페이지 파싱하여 게시글 데이터 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        data = []
        
        logging.info(f"[{category}] 파싱 시작 - HTML 크기: {len(html)} bytes")
        
        # 새로운 swuniv.jbnu.ac.kr 사이트 구조 (우선순위 높음)
        if 'SW중심대학사업단' in category:
            logging.info(f"[{category}] swuniv.jbnu.ac.kr 사이트 구조로 파싱")
            return self._parse_swuniv_page(soup, category)
        
        # 기존 csai.jbnu.ac.kr 사이트 구조
        elif 'csai.jbnu.ac.kr' in category or '학과소식' in category or '일반공지' in category or '학사공지' in category or '사업단공지' in category or '취업정보' in category:
            logging.info(f"[{category}] csai.jbnu.ac.kr 사이트 구조로 파싱")
            return self._parse_csai_page(soup, category)
        
        else:
            logging.warning(f"[{category}] 알 수 없는 사이트 구조입니다.")
            return []
    
    def _parse_csai_page(self, soup, category):
        """기존 csai.jbnu.ac.kr 사이트 파싱"""
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
            
            # 고유 ID 생성 (URL 기반)
            notice_id = f"{category}_{number}_{hash(full_url) % 100000}"
            
            post_data = {
                'id': notice_id,
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
    
    def _parse_swuniv_page(self, soup, category):
        """새로운 swuniv.jbnu.ac.kr 사이트 파싱 (프로그램 신청 페이지)"""
        data = []
        
        # 프로그램 신청 페이지는 테이블 구조가 아닌 링크 기반 구조
        logging.info(f"[{category}] 프로그램 신청 페이지 파싱 시작")
        
        # 프로그램 링크 찾기
        program_links = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # 프로그램 관련 링크 필터링 (신청하기, 접수마감 등)
            if ('신청하기' in text or '접수마감' in text) and text and len(text) > 10:
                # 상대 URL을 절대 URL로 변환
                if href.startswith('/'):
                    full_url = 'https://swuniv.jbnu.ac.kr' + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://swuniv.jbnu.ac.kr/main/{href}"
                
                program_links.append({
                    'href': full_url,
                    'text': text
                })
        
        logging.info(f"[{category}] 프로그램 링크 {len(program_links)}개 발견")
        
        # 각 프로그램 정보 파싱
        for i, link in enumerate(program_links):
            try:
                # 제목 추출 (링크 텍스트에서)
                title = link['text']
                
                # 카테고리 정보 추출 (제목에서)
                program_category = '프로그램'
                if 'SW가치확산' in title:
                    program_category = 'SW가치확산'
                elif 'SW융합' in title:
                    program_category = 'SW융합'
                elif 'SW전공' in title:
                    program_category = 'SW전공'
                elif '산학협력' in title:
                    program_category = '산학협력'
                elif '교육환경지원' in title:
                    program_category = '교육환경지원'
                
                # 고유 ID 생성
                notice_id = f"{category}_{i+1}_{hash(link['href']) % 100000}"
                
                post_data = {
                    'id': notice_id,
                    'category': f"{category}_{program_category}",
                    'number': str(i+1),
                    'title': title,
                    'author': 'SW중심대학사업단',
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'attachments': '',
                    'views': '0',
                    'url': link['href'],
                    'content': '',
                    'content_html': '',
                    'image_urls': [],
                    'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                data.append(post_data)
                
            except Exception as e:
                logging.warning(f"[{category}] 프로그램 파싱 중 오류: {e}")
                continue
        
        return data
    
    def _parse_swuniv_alternative(self, soup, category):
        """SW중심대학사업단 사이트 대체 파싱 방법"""
        data = []
        
        # 링크 기반으로 공지사항 찾기 (view가 포함된 링크)
        links = soup.find_all('a', href=True)
        notice_count = 0
        
        for link in links:
            href = link.get('href', '')
            title = link.get_text().strip()
            
            # view가 포함된 링크만 처리 (실제 공지사항 링크)
            if 'view' in href and 'bwrite_id' in href and title and len(title) > 5:
                # URL 정규화
                if href.startswith('/'):
                    full_url = 'https://swuniv.jbnu.ac.kr' + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://swuniv.jbnu.ac.kr/main/{href}"
                
                notice_count += 1
                notice_id = f"{category}_{notice_count}_{hash(full_url) % 100000}"
                
                # URL에서 날짜 정보 추출 시도
                date_str = datetime.now().strftime("%Y-%m-%d")
                
                post_data = {
                    'id': notice_id,
                    'category': category,
                    'number': str(notice_count),
                    'title': title,
                    'author': '관리자',
                    'date': date_str,
                    'attachments': '',
                    'views': '0',
                    'url': full_url,
                    'content': '',
                    'content_html': '',
                    'image_urls': [],
                    'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                data.append(post_data)
        
        logging.info(f"[{category}] 링크 기반 파싱으로 {len(data)}개 공지사항 추출")
        return data

    def get_post_content(self, url):
        """게시글 상세 내용, HTML 원문, 이미지 URL들 가져오기"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_text = ''
            content_html = ''
            image_urls = []
            
            # 기존 csai.jbnu.ac.kr 사이트 구조
            if 'csai.jbnu.ac.kr' in url:
                return self._get_csai_content(soup, url)
            
            # 새로운 swuniv.jbnu.ac.kr 사이트 구조
            elif 'swuniv.jbnu.ac.kr' in url:
                return self._get_swuniv_content(soup, url)
            
            # 기본 구조 시도
            else:
                return self._get_default_content(soup, url)
                
        except Exception as e:
            logging.error(f"상세 내용 가져오기 실패 ({url}): {e}")
            return {
                'content_text': '',
                'content_html': '',
                'image_urls': []
            }
    
    def _get_csai_content(self, soup, url):
        """기존 csai.jbnu.ac.kr 사이트 내용 추출"""
        content_text = ''
        content_html = ''
        image_urls = []
        base_url = self.get_base_url(url)
        
        # artclView div에서 내용 추출
        artcl_view = soup.find('div', class_='artclView')
        if artcl_view:
            content_html = str(artcl_view)
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
                    full_img_url = urljoin(base_url, src)
                    image_urls.append(full_img_url)
        
        # hwp_editor_board_content div에서 내용 추출
        if not content_text:
            hwp_content = soup.find('div', class_='hwp_editor_board_content')
            if hwp_content:
                content_html = str(hwp_content)
                content_text = hwp_content.get_text()
                content_text = ' '.join(content_text.split())
                
                img_tags = hwp_content.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        full_img_url = urljoin(base_url, src)
                        image_urls.append(full_img_url)
        
        return {
            'content_text': content_text,
            'content_html': content_html,
            'image_urls': image_urls
        }
    
    def _get_swuniv_content(self, soup, url):
        """새로운 swuniv.jbnu.ac.kr 사이트 내용 추출"""
        content_text = ''
        content_html = ''
        image_urls = []
        
        # SW중심대학사업단 사이트의 내용 구조 분석
        # 다양한 가능한 컨텐츠 영역 시도
        content_selectors = [
            'div.content',
            'div.article-content',
            'div.board-content',
            'div.view-content',
            'div.post-content',
            'div.main-content',
            'div.text-content',
            'div.body-content',
            'div.entry-content',
            'div.article-body',
            'div.board-view',
            'div.view'
        ]
        
        for selector in content_selectors:
            content_div = soup.find('div', class_=selector)
            if content_div:
                content_html = str(content_div)
                content_text = content_div.get_text()
                content_text = ' '.join(content_text.split())
                
                # 이미지 URL들 추출
                img_tags = content_div.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        if src.startswith('/'):
                            full_img_url = 'https://swuniv.jbnu.ac.kr' + src
                        elif src.startswith('http'):
                            full_img_url = src
                        else:
                            full_img_url = 'https://swuniv.jbnu.ac.kr/' + src
                        image_urls.append(full_img_url)
                
                if content_text and len(content_text.strip()) > 10:
                    break
        
        # 위 방법으로 찾지 못한 경우, 모든 텍스트 추출
        if not content_text:
            # 메인 컨텐츠 영역 찾기
            main_content = soup.find('main') or soup.find('article') or soup.find('div', id='content')
            if main_content:
                content_html = str(main_content)
                content_text = main_content.get_text()
                content_text = ' '.join(content_text.split())
                
                # 이미지 URL들 추출
                img_tags = main_content.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        if src.startswith('/'):
                            full_img_url = 'https://swuniv.jbnu.ac.kr' + src
                        elif src.startswith('http'):
                            full_img_url = src
                        else:
                            full_img_url = 'https://swuniv.jbnu.ac.kr/' + src
                        image_urls.append(full_img_url)
        
        return {
            'content_text': content_text,
            'content_html': content_html,
            'image_urls': image_urls
        }
    
    def _get_default_content(self, soup, url):
        """기본 내용 추출 방법"""
        content_text = ''
        content_html = ''
        image_urls = []
        
        # 일반적인 컨텐츠 영역 찾기
        content_div = soup.find('div', class_='content') or soup.find('div', class_='article') or soup.find('div', class_='post')
        
        if content_div:
            content_html = str(content_div)
            content_text = content_div.get_text()
            content_text = ' '.join(content_text.split())
            
            # 이미지 URL들 추출
            img_tags = content_div.find_all('img')
            for img in img_tags:
                src = img.get('src')
                if src:
                    full_img_url = urljoin(url, src)
                    image_urls.append(full_img_url)
        
        return {
            'content_text': content_text,
            'content_html': content_html,
            'image_urls': image_urls
        }

    def crawl_single_url(self, url, category, max_pages=2):
        """단일 URL 크롤링"""
        logging.info(f"[{category}] 크롤링 시작: {url}")
        url_data = []
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            total_pages = self.get_total_pages(soup, url)
            
            logging.info(f"[{category}] 총 {total_pages}페이지 크롤링 예정")
            
            for page_num in range(1, total_pages + 1):
                # URL별 파라미터 처리
                if 'swuniv.jbnu.ac.kr' in url:
                    # SW중심대학사업단 사이트는 URL에 페이지 파라미터 추가
                    if '?' in url:
                        page_url = f"{url}&page={page_num}"
                    else:
                        page_url = f"{url}?page={page_num}"
                    response = requests.get(page_url, timeout=10)
                else:
                    # 기존 csai.jbnu.ac.kr 사이트는 파라미터 방식
                    params = {'page': page_num}
                    response = requests.get(url, params=params, timeout=10)
                
                try:
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
        """모든 URL을 크롤링"""
        logging.info("다중 URL 크롤링 시작...")
        start_time = time.time()
        all_data = []
        
        if use_threading:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_url = {
                    executor.submit(self.crawl_single_url, url, category, max_pages): (url, category)
                    for url, category in self.target_urls.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_url):
                    url, category = future_to_url[future]
                    try:
                        url_data = future.result()
                        all_data.extend(url_data)
                        logging.info(f"[{category}] {len(url_data)}개 게시글 수집 완료")
                    except Exception as e:
                        logging.error(f"[{category}] 크롤링 실패: {e}")
        else:
            for url, category in self.target_urls.items():
                url_data = self.crawl_single_url(url, category, max_pages)
                all_data.extend(url_data)
        
        end_time = time.time()
        logging.info(f"전체 크롤링 완료: {len(all_data)}개 게시글, 소요시간: {end_time - start_time:.2f}초")
        
        return all_data

    def find_new_posts(self, current_data):
        """새로운 게시글 찾기"""
        existing_urls = {post.get('url', '') for post in self.existing_data if post.get('url')}
        
        new_posts = []
        for post in current_data:
            if post.get('url') and post['url'] not in existing_urls:
                new_posts.append(post)
                logging.info(f"새 게시글 발견: [{post.get('category', 'Unknown')}] {post.get('title', 'N/A')[:50]}...")
        
        return new_posts

    def save_data(self):
        """데이터를 JSON 파일로 저장"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.existing_data, f, ensure_ascii=False, indent=2)
            logging.info(f"데이터 저장 완료: {self.data_file}")
        except Exception as e:
            logging.error(f"데이터 저장 실패: {e}")

    # 비동기 메서드들
    async def get_notices(self, category: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> List[NoticeResponse]:
        """공지사항 목록 조회"""
        with self.data_lock:
            data = self.existing_data.copy()
        
        # 카테고리 필터링
        if category:
            data = [post for post in data if post.get('category') == category]
        
        # 정렬 (최신순)
        data = sorted(data, key=lambda x: x.get('date', ''), reverse=True)
        
        # 페이징
        if offset:
            data = data[offset:]
        if limit:
            data = data[:limit]
        
        return [NoticeResponse(**post) for post in data]

    async def get_notice_by_id(self, notice_id: str) -> Optional[NoticeResponse]:
        """특정 공지사항 조회"""
        with self.data_lock:
            for post in self.existing_data:
                if post.get('id') == notice_id:
                    return NoticeResponse(**post)
        return None

    async def get_categories(self) -> List[str]:
        """카테고리 목록 조회"""
        with self.data_lock:
            categories = list(set(post.get('category', 'Unknown') for post in self.existing_data))
        return sorted(categories)

    async def get_summary(self) -> List[CategorySummary]:
        """카테고리별 요약 정보 조회"""
        with self.data_lock:
            summary_dict = {}
            for post in self.existing_data:
                category = post.get('category', 'Unknown')
                if category not in summary_dict:
                    summary_dict[category] = {'count': 0, 'dates': []}
                summary_dict[category]['count'] += 1
                summary_dict[category]['dates'].append(post.get('date', ''))
        
        summary = []
        for category, data in summary_dict.items():
            latest_date = max(data['dates']) if data['dates'] else None
            summary.append(CategorySummary(
                category=category,
                count=data['count'],
                latest_date=latest_date
            ))
        
        return sorted(summary, key=lambda x: x.count, reverse=True)

    async def search_notices(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[NoticeResponse]:
        """공지사항 검색"""
        with self.data_lock:
            data = self.existing_data.copy()
        
        # 카테고리 필터링
        if category:
            data = [post for post in data if post.get('category') == category]
        
        # 검색어 필터링
        query_lower = query.lower()
        filtered_data = []
        for post in data:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            if query_lower in title or query_lower in content:
                filtered_data.append(post)
        
        # 정렬 및 제한
        filtered_data = sorted(filtered_data, key=lambda x: x.get('date', ''), reverse=True)
        if limit:
            filtered_data = filtered_data[:limit]
        
        return [NoticeResponse(**post) for post in filtered_data]

    async def get_latest_notices(self, limit: int = 10) -> List[NoticeResponse]:
        """최신 공지사항 조회"""
        with self.data_lock:
            data = sorted(self.existing_data, key=lambda x: x.get('date', ''), reverse=True)
        
        return [NoticeResponse(**post) for post in data[:limit]]

    async def crawl_new_posts(self):
        """새로운 게시글만 크롤링 (백그라운드)"""
        self.crawl_status = "running"
        try:
            logging.info("새로운 게시글 확인 시작...")
            
            # 모든 URL에서 최신 데이터 수집
            current_data = self.crawl_all_urls(max_pages=self.max_pages, use_threading=True)
            
            # 새로운 게시글 찾기
            new_posts = self.find_new_posts(current_data)
            
            if new_posts:
                # 새로운 데이터를 기존 데이터 앞에 추가
                with self.data_lock:
                    self.existing_data = new_posts + self.existing_data
                    self.save_data()
                
                # Firebase에 새 게시글 저장
                if self.firebase_enabled and self.firebase_service.is_initialized():
                    try:
                        firebase_result = await self.firebase_service.save_notices_batch(new_posts)
                        logging.info(f"Firebase 저장 완료: 성공 {firebase_result['success']}개, 실패 {firebase_result['failed']}개")
                    except Exception as e:
                        logging.error(f"Firebase 저장 실패: {e}")
                
                logging.info(f"새로운 게시글 {len(new_posts)}개 발견 및 저장 완료")
            else:
                logging.info("새로운 게시글이 없습니다.")
            
            self.crawl_status = "completed"
            self.last_crawl_time = datetime.now().isoformat()
            
        except Exception as e:
            logging.error(f"크롤링 중 오류 발생: {e}")
            self.crawl_status = "error"

    async def crawl_all_posts(self):
        """전체 크롤링 실행 (백그라운드)"""
        self.crawl_status = "running"
        try:
            logging.info("전체 크롤링 시작...")
            
            all_data = self.crawl_all_urls(max_pages=self.max_pages, use_threading=True)
            
            with self.data_lock:
                self.existing_data = all_data
                self.save_data()
            
            # Firebase에 전체 데이터 저장
            if self.firebase_enabled and self.firebase_service.is_initialized():
                try:
                    firebase_result = await self.firebase_service.save_notices_batch(all_data)
                    logging.info(f"Firebase 전체 저장 완료: 성공 {firebase_result['success']}개, 실패 {firebase_result['failed']}개")
                except Exception as e:
                    logging.error(f"Firebase 전체 저장 실패: {e}")
            
            logging.info(f"전체 크롤링 완료: {len(all_data)}개 게시글")
            self.crawl_status = "completed"
            self.last_crawl_time = datetime.now().isoformat()
            
        except Exception as e:
            logging.error(f"전체 크롤링 중 오류 발생: {e}")
            self.crawl_status = "error"

    async def get_crawl_status(self) -> CrawlStatus:
        """크롤링 상태 조회"""
        with self.data_lock:
            total_notices = len(self.existing_data)
        
        return CrawlStatus(
            status=self.crawl_status,
            message=f"현재 상태: {self.crawl_status}",
            timestamp=datetime.now().isoformat(),
            last_crawl_time=self.last_crawl_time,
            total_notices=total_notices
        )
    
    def start_scheduler(self):
        """스케줄러 시작"""
        self.scheduler_service.start()
        logging.info("스케줄러가 시작되었습니다.")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        self.scheduler_service.stop()
        logging.info("스케줄러가 중지되었습니다.")
    
    def get_scheduler_status(self) -> dict:
        """스케줄러 상태 조회"""
        return self.scheduler_service.get_status()
    
    def update_crawl_interval(self, minutes: int) -> bool:
        """크롤링 간격 업데이트"""
        return self.scheduler_service.update_interval(minutes)
    
    def run_crawl_now(self) -> bool:
        """즉시 크롤링 실행"""
        return self.scheduler_service.run_now()
    
    async def get_firebase_stats(self) -> dict:
        """Firebase 통계 정보 조회"""
        if not self.firebase_enabled or not self.firebase_service.is_initialized():
            return {"error": "Firebase가 초기화되지 않았거나 비활성화되어 있습니다."}
        
        return await self.firebase_service.get_collection_stats()
    
    async def sync_to_firebase(self) -> dict:
        """로컬 데이터를 Firebase에 동기화"""
        if not self.firebase_enabled or not self.firebase_service.is_initialized():
            return {"error": "Firebase가 초기화되지 않았거나 비활성화되어 있습니다."}
        
        with self.data_lock:
            data = self.existing_data.copy()
        
        if not data:
            return {"message": "동기화할 데이터가 없습니다.", "success": 0, "failed": 0}
        
        try:
            result = await self.firebase_service.save_notices_batch(data)
            logging.info(f"Firebase 동기화 완료: 성공 {result['success']}개, 실패 {result['failed']}개")
            return result
        except Exception as e:
            logging.error(f"Firebase 동기화 실패: {e}")
            return {"error": str(e), "success": 0, "failed": len(data)}
    
    async def test_firebase_connection(self) -> dict:
        """Firebase 연결 테스트"""
        if not self.firebase_enabled:
            return {"error": "Firebase 동기화가 비활성화되어 있습니다."}
        
        if not self.firebase_service.is_initialized():
            return {"error": "Firebase가 초기화되지 않았습니다."}
        
        try:
            is_connected = self.firebase_service.test_connection()
            if is_connected:
                return {"status": "success", "message": "Firebase 연결 성공"}
            else:
                return {"status": "error", "message": "Firebase 연결 실패"}
        except Exception as e:
            return {"status": "error", "message": f"Firebase 연결 테스트 실패: {e}"}
