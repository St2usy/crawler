import requests
from bs4 import BeautifulSoup

def debug_html_structure():
    """
    Debug function to analyze the HTML structure of the page
    """
    url = 'https://csai.jbnu.ac.kr/csai/29105/subview.do'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table
        table = soup.find('table', class_='artclTable')
        if table:
            print("✅ artclTable을 찾았습니다!")
            
            # Find tbody
            tbody = table.find('tbody')
            if tbody:
                print("✅ tbody를 찾았습니다!")
                
                # Get all rows
                rows = tbody.find_all('tr')
                print(f"총 {len(rows)}개의 행을 찾았습니다.")
                
                # Analyze first few rows
                for i, row in enumerate(rows[:3]):
                    print(f"\n--- 행 {i+1} 분석 ---")
                    print(f"클래스: {row.get('class', [])}")
                    
                    cols = row.find_all('td')
                    print(f"열 개수: {len(cols)}")
                    
                    for j, col in enumerate(cols):
                        text = col.get_text(strip=True)
                        print(f"  열 {j}: '{text}'")
                        
                        # Check for links in title column
                        if j == 1:  # Title column
                            links = col.find_all('a')
                            if links:
                                for link in links:
                                    print(f"    링크: {link.get('href', '')}")
                                    print(f"    링크 텍스트: '{link.get_text(strip=True)}'")
            else:
                print("❌ tbody를 찾을 수 없습니다!")
        else:
            print("❌ artclTable을 찾을 수 없습니다!")
            
            # Try to find any table
            tables = soup.find_all('table')
            print(f"전체 테이블 개수: {len(tables)}")
            for i, table in enumerate(tables):
                print(f"테이블 {i+1} 클래스: {table.get('class', [])}")
                
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    debug_html_structure()
