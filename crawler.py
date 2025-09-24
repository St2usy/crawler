import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
from datetime import datetime

# 웹페이지 URL
BASE_URL = 'https://csai.jbnu.ac.kr'

def get_total_pages(soup):
    """
    Get the total number of pages from the pagination section.
    """
    paging_div = soup.find('div', class_='_paging')
    if paging_div:
        total_page_span = paging_div.find('span', class_='_totPage')
        if total_page_span:
            # Extract only the number from the text
            return int(re.search(r'\d+', total_page_span.text).group())
    return 1

def parse_page(html):
    """
    Parse a single page and extract post data.
    """
    soup = BeautifulSoup(html, 'html.parser')
    data = []
    
    # Find the table containing the posts
    table = soup.find('table', class_='artclTable')
    if not table:
        print("공지사항 테이블을 찾을 수 없습니다.")
        return []
    
    # Find all table rows (<tr>) except the header row (<th>)
    rows = table.find('tbody').find_all('tr')
    
    for row in rows:
        # Skip empty rows or rows without enough columns
        cols = row.find_all('td')
        if len(cols) < 6:
            continue
            
        # Extract number
        number = cols[0].text.strip()
        
        # Extract title and link
        title_cell = cols[1]
        title_link = title_cell.find('a')
        if title_link:
            # Clean title text by removing extra whitespace and newlines
            title = title_link.get_text()
            title = ' '.join(title.split())  # Remove extra whitespace and newlines
            # Extract link URL
            href = title_link.get('href', '')
            full_url = urljoin(BASE_URL, href) if href else ''
        else:
            title = title_cell.get_text()
            title = ' '.join(title.split())  # Remove extra whitespace and newlines
            full_url = ''
        
        # Extract author
        author = cols[2].text.strip()
        
        # Extract date
        date = cols[3].text.strip()
        
        # Extract attachments
        attachments = cols[4].text.strip()
        
        # Extract views
        views = cols[5].text.strip()
        
        post_data = {
            'number': number,
            'title': title,
            'author': author,
            'date': date,
            'attachments': attachments,
            'views': views,
            'url': full_url
        }
        data.append(post_data)
    return data

def get_post_content(url):
    """
    Get the detailed content of a post from its URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find content in various possible locations
        content_text = ''
        
        # Method 1: Look for artclView div (most reliable based on debugging)
        artcl_view = soup.find('div', class_='artclView')
        if artcl_view:
            # Get all text from artclView and clean it
            content_text = artcl_view.get_text()
            # Clean up the text by removing extra whitespace and newlines
            content_text = ' '.join(content_text.split())
            # Remove the title part if it's duplicated at the beginning
            lines = content_text.split()
            if len(lines) > 10:  # If content is long enough
                # Try to find where actual content starts (skip title repetition)
                content_text = ' '.join(lines[5:])  # Skip first few words that might be title
        
        # Method 2: Look for hwp_editor_board_content div
        if not content_text:
            hwp_content = soup.find('div', class_='hwp_editor_board_content')
            if hwp_content:
                content_text = hwp_content.get_text()
                content_text = ' '.join(content_text.split())
        
        # Method 3: Look for board_view div
        if not content_text:
            board_view = soup.find('div', class_='board_view')
            if board_view:
                content_div = board_view.find('div', class_='view_content')
                if content_div:
                    content_text = content_div.get_text()
                    content_text = ' '.join(content_text.split())
        
        # Method 4: Look for any div with view_content class
        if not content_text:
            content_div = soup.find('div', class_='view_content')
            if content_div:
                content_text = content_div.get_text()
                content_text = ' '.join(content_text.split())
        
        # Method 5: Look for content in table structure (fallback)
        if not content_text:
            content_table = soup.find('table', class_='artclTable')
            if content_table:
                content_cells = content_table.find_all('td')
                for cell in content_cells:
                    cell_text = cell.get_text()
                    clean_cell_text = ' '.join(cell_text.split())
                    if len(clean_cell_text) > 100:  # Likely content cell
                        content_text = clean_cell_text
                        break
        
        return {
            'content': content_text,
            'url': url
        }
        
    except Exception as e:
        print(f"상세 내용 가져오기 중 오류 발생 ({url}): {e}")
        return None

def save_to_json(data, filename=None):
    """Save data to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jbnu_notices_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON 파일로 저장 완료: {filename}")
    return filename

def main():
    """
    Main function to crawl the bulletin board and save data to JSON.
    """
    print("전북대학교 컴퓨터인공지능학부 공지사항 크롤링을 시작합니다...")
    all_data = []
    
    # Get initial page to find total pages
    response = requests.get('https://csai.jbnu.ac.kr/csai/29107/subview.do')
    if response.status_code != 200:
        print(f"Failed to access the page: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    total_pages = get_total_pages(soup)
    total_pages = 2
    print(f"총 {total_pages}페이지를 크롤링합니다.")
    
    for page_num in range(1, total_pages + 1):
        # Construct the URL for each page
        params = {
            'page': page_num
        }
        
        # Requests a page with parameters and get response
        try:
            response = requests.get('https://csai.jbnu.ac.kr/csai/29107/subview.do', params=params)
            response.raise_for_status()
            
            # Parse the current page
            print(f"페이지 {page_num}/{total_pages} 크롤링 중...")
            page_data = parse_page(response.text)
            
            # Get detailed content for each post
            for i, post in enumerate(page_data):
                if post['url']:
                    print(f"  {i+1}/{len(page_data)}: {post['title'][:50]}... 상세 내용 수집 중...")
                    content_data = get_post_content(post['url'])
                    if content_data:
                        post['content'] = content_data['content']
                    time.sleep(0.5)  # 서버 부하 방지
            
            all_data.extend(page_data)
            print(f"페이지 {page_num} 완료: {len(page_data)}개 공지사항 수집")
            time.sleep(1)  # 서버 부하 방지
        
        except requests.exceptions.RequestException as e:
            print(f"페이지 {page_num} 크롤링 중 오류 발생: {e}")
            break

    # Save data to JSON file
    if all_data:
        save_to_json(all_data)
        print(f"\n크롤링 완료! 총 {len(all_data)}개 공지사항이 JSON 파일로 저장되었습니다.")
        
        # Show summary
        print("\n수집된 공지사항 요약:")
        for i, post in enumerate(all_data[:5], 1):
            print(f"{i}. [{post['date']}] {post['title']}")
            if post.get('content'):
                print(f"   내용: {post['content'][:100]}...")
            print()
    else:
        print("\n수집할 데이터가 없습니다. 크롤링 과정에서 문제가 발생했을 수 있습니다.")

if __name__ == "__main__":
    main()