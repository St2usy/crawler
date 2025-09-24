import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def test_simple_parse():
    """
    Simple test to parse just the first few posts
    """
    url = 'https://csai.jbnu.ac.kr/csai/29105/subview.do'
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', class_='artclTable')
    rows = table.find('tbody').find_all('tr')
    
    print("=== 테이블 행 분석 ===")
    for i, row in enumerate(rows[:3]):
        print(f"\n--- 행 {i+1} ---")
        print(f"클래스: {row.get('class', [])}")
        
        cols = row.find_all('td')
        print(f"열 개수: {len(cols)}")
        
        if len(cols) >= 6:
            print(f"번호: '{cols[0].text.strip()}'")
            print(f"제목: '{cols[1].text.strip()}'")
            print(f"작성자: '{cols[2].text.strip()}'")
            print(f"날짜: '{cols[3].text.strip()}'")
            print(f"첨부: '{cols[4].text.strip()}'")
            print(f"조회수: '{cols[5].text.strip()}'")
            
            # 링크 확인
            title_link = cols[1].find('a')
            if title_link:
                print(f"링크: {title_link.get('href', '')}")
                print(f"링크 텍스트: '{title_link.get_text(strip=True)}'")

if __name__ == "__main__":
    test_simple_parse()
