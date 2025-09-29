#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
군산대학교 SW 사업단 사이트 접근성 테스트
다양한 방법으로 SSL 문제를 우회하여 접근을 시도합니다.
"""

import requests
from bs4 import BeautifulSoup
import json
import ssl
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import warnings

# 경고 비활성화
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_url_access(url, method_name, session=None):
    """URL 접근 테스트"""
    print(f"\n=== {method_name} 시도 ===")
    print(f"URL: {url}")
    
    try:
        if session:
            response = session.get(url, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        
        print(f"응답 상태: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"페이지 제목: {soup.title.text if soup.title else 'N/A'}")
            
            # HTML 구조 분석
            tables = soup.find_all('table')
            divs = soup.find_all('div')
            links = soup.find_all('a', href=True)
            
            print(f"테이블 개수: {len(tables)}")
            print(f"Div 개수: {len(divs)}")
            print(f"링크 개수: {len(links)}")
            
            # 내용 미리보기
            content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            print(f"내용 미리보기: {content_preview}")
            
            return {
                'method': method_name,
                'status': 'success',
                'status_code': response.status_code,
                'title': soup.title.text if soup.title else '',
                'tables_count': len(tables),
                'content_length': len(response.text)
            }
        else:
            print(f"HTTP 오류: {response.status_code}")
            return {
                'method': method_name,
                'status': 'http_error',
                'status_code': response.status_code
            }
            
    except Exception as e:
        print(f"오류 발생: {e}")
        return {
            'method': method_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    """메인 함수"""
    test_urls = [
        'https://sw.kunsan.ac.kr/main/sw?gc=605XOAS&sca=',
        'https://sw.kunsan.ac.kr/main/sw?gc=483ZJFR',
        'https://sw.kunsan.ac.kr/main/sw?gc=Program'
    ]
    
    results = []
    
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"테스트 URL: {url}")
        print(f"{'='*80}")
        
        url_results = []
        
        # 방법 1: 기본 요청 (SSL 검증 비활성화)
        result1 = test_url_access(url, "SSL 검증 비활성화", None)
        url_results.append(result1)
        
        # 방법 2: 커스텀 세션으로 SSL 설정
        try:
            session = requests.Session()
            session.verify = False
            
            # SSL 컨텍스트 설정
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            session.mount('https://', requests.adapters.HTTPAdapter())
            
            result2 = test_url_access(url, "커스텀 SSL 컨텍스트", session)
            url_results.append(result2)
        except Exception as e:
            print(f"커스텀 SSL 설정 실패: {e}")
            url_results.append({
                'method': "커스텀 SSL 컨텍스트",
                'status': 'error',
                'error': str(e)
            })
        
        # 방법 3: HTTP로 리다이렉트 시도
        http_url = url.replace('https://', 'http://')
        result3 = test_url_access(http_url, "HTTP 리다이렉트", None)
        url_results.append(result3)
        
        # 방법 4: 다양한 User-Agent 시도
        headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'},
            {'User-Agent': 'curl/7.68.0'},
            {'User-Agent': 'Python-requests/2.25.1'}
        ]
        
        for i, headers in enumerate(headers_list):
            try:
                response = requests.get(url, headers=headers, verify=False, timeout=15)
                result = {
                    'method': f"User-Agent {i+1}",
                    'status': 'success' if response.status_code == 200 else 'http_error',
                    'status_code': response.status_code
                }
                url_results.append(result)
                print(f"User-Agent {i+1}: {response.status_code}")
            except Exception as e:
                url_results.append({
                    'method': f"User-Agent {i+1}",
                    'status': 'error',
                    'error': str(e)
                })
        
        results.append({
            'url': url,
            'tests': url_results
        })
    
    # 결과를 JSON 파일로 저장
    with open('sw_kunsan_access_test.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("테스트 완료!")
    print("결과가 sw_kunsan_access_test.json 파일에 저장되었습니다.")
    
    # 요약 출력
    print(f"\n=== 요약 ===")
    for result in results:
        url = result['url']
        success_count = sum(1 for test in result['tests'] if test['status'] == 'success')
        print(f"{url}: {success_count}/{len(result['tests'])} 성공")

if __name__ == "__main__":
    main()
