#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
다중 URL 크롤러 테스트 스크립트
"""

from multi_url_crawler import MultiURLCrawler
import json
import time

def test_single_url():
    """
    단일 URL 크롤링 테스트
    """
    print("=== 단일 URL 크롤링 테스트 ===")
    
    crawler = MultiURLCrawler()
    
    # 학과소식만 테스트
    test_url = 'https://csai.jbnu.ac.kr/csai/29105/subview.do'
    test_category = '학과소식'
    
    print(f"테스트 URL: {test_url}")
    print(f"카테고리: {test_category}")
    
    start_time = time.time()
    data = crawler.crawl_single_url(test_url, test_category, max_pages=1)
    end_time = time.time()
    
    print(f"수집된 게시글 수: {len(data)}개")
    print(f"소요시간: {end_time - start_time:.2f}초")
    
    if data:
        print("\n=== 수집된 게시글 샘플 ===")
        for i, post in enumerate(data[:3], 1):
            print(f"{i}. [{post.get('date', 'N/A')}] {post.get('title', 'N/A')}")
    
    return data

def test_multi_url():
    """
    다중 URL 크롤링 테스트
    """
    print("\n=== 다중 URL 크롤링 테스트 ===")
    
    crawler = MultiURLCrawler()
    
    start_time = time.time()
    data = crawler.crawl_all_urls(max_pages=1, use_threading=True)
    end_time = time.time()
    
    print(f"총 수집된 게시글 수: {len(data)}개")
    print(f"소요시간: {end_time - start_time:.2f}초")
    
    # 카테고리별 요약
    summary = crawler.get_summary_by_category()
    print("\n=== 카테고리별 수집 현황 ===")
    for category, count in summary.items():
        print(f"- {category}: {count}개")
    
    # JSON 저장 테스트
    filename = crawler.save_to_json("test_multi_notices.json")
    if filename:
        print(f"\n테스트 데이터가 {filename}에 저장되었습니다.")
    
    return data

def test_sequential_vs_parallel():
    """
    순차 처리 vs 병렬 처리 성능 비교
    """
    print("\n=== 성능 비교 테스트 ===")
    
    crawler = MultiURLCrawler()
    
    # 순차 처리 테스트
    print("순차 처리 테스트 중...")
    start_time = time.time()
    sequential_data = crawler.crawl_all_urls(max_pages=1, use_threading=False)
    sequential_time = time.time() - start_time
    
    # 데이터 초기화
    crawler.all_data = []
    
    # 병렬 처리 테스트
    print("병렬 처리 테스트 중...")
    start_time = time.time()
    parallel_data = crawler.crawl_all_urls(max_pages=1, use_threading=True)
    parallel_time = time.time() - start_time
    
    print(f"\n=== 성능 비교 결과 ===")
    print(f"순차 처리: {sequential_time:.2f}초, {len(sequential_data)}개 게시글")
    print(f"병렬 처리: {parallel_time:.2f}초, {len(parallel_data)}개 게시글")
    print(f"성능 향상: {((sequential_time - parallel_time) / sequential_time * 100):.1f}%")

def main():
    """
    메인 테스트 함수
    """
    print("전북대학교 컴퓨터인공지능학부 다중 URL 크롤러 테스트")
    print("=" * 60)
    
    try:
        # 1. 단일 URL 테스트
        single_data = test_single_url()
        
        # 2. 다중 URL 테스트
        multi_data = test_multi_url()
        
        # 3. 성능 비교 테스트 (선택사항)
        print("\n성능 비교 테스트를 실행하시겠습니까? (y/n): ", end="")
        if input().lower() == 'y':
            test_sequential_vs_parallel()
        
        print("\n=== 테스트 완료 ===")
        print("모든 테스트가 성공적으로 완료되었습니다.")
        
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
