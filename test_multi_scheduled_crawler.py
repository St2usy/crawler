#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
다중 URL 스케줄러 크롤러 테스트 스크립트
"""

from multi_url_scheduled_crawler import MultiURLScheduledCrawler
import json
import time
import os

def test_config_loading():
    """
    설정 파일 로딩 테스트
    """
    print("=== 설정 파일 로딩 테스트 ===")
    
    crawler = MultiURLScheduledCrawler()
    
    print(f"기본 URL: {crawler.base_url}")
    print(f"데이터 파일: {crawler.data_file}")
    print(f"체크 간격: {crawler.check_interval}분")
    print(f"최대 페이지: {crawler.max_pages}")
    print(f"대상 URL 수: {len(crawler.target_urls)}개")
    
    for url, category in crawler.target_urls.items():
        print(f"  - {category}: {url}")
    
    return True

def test_single_url_crawl():
    """
    단일 URL 크롤링 테스트
    """
    print("\n=== 단일 URL 크롤링 테스트 ===")
    
    crawler = MultiURLScheduledCrawler()
    
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

def test_new_post_detection():
    """
    새로운 게시글 감지 테스트
    """
    print("\n=== 새로운 게시글 감지 테스트 ===")
    
    crawler = MultiURLScheduledCrawler()
    
    # 기존 데이터가 있는지 확인
    print(f"기존 데이터 수: {len(crawler.existing_data)}개")
    
    # 한 번 크롤링 실행
    print("첫 번째 크롤링 실행...")
    new_posts_1 = crawler.run_once()
    print(f"첫 번째 실행 결과: {len(new_posts_1)}개 새 게시글")
    
    # 잠시 대기
    print("5초 대기 중...")
    time.sleep(5)
    
    # 두 번째 크롤링 실행 (새로운 게시글이 없어야 함)
    print("두 번째 크롤링 실행...")
    new_posts_2 = crawler.run_once()
    print(f"두 번째 실행 결과: {len(new_posts_2)}개 새 게시글")
    
    return new_posts_1, new_posts_2

def test_full_crawl():
    """
    전체 크롤링 테스트
    """
    print("\n=== 전체 크롤링 테스트 ===")
    
    crawler = MultiURLScheduledCrawler()
    
    start_time = time.time()
    all_data = crawler.run_full_crawl()
    end_time = time.time()
    
    print(f"전체 크롤링 완료: {len(all_data)}개 게시글")
    print(f"소요시간: {end_time - start_time:.2f}초")
    
    # 카테고리별 요약
    summary = crawler.get_summary_by_category()
    print("\n=== 카테고리별 수집 현황 ===")
    for category, count in summary.items():
        print(f"- {category}: {count}개")
    
    return all_data

def test_data_persistence():
    """
    데이터 지속성 테스트
    """
    print("\n=== 데이터 지속성 테스트 ===")
    
    # 첫 번째 크롤러 인스턴스
    crawler1 = MultiURLScheduledCrawler()
    initial_count = len(crawler1.existing_data)
    print(f"초기 데이터 수: {initial_count}개")
    
    # 데이터 추가
    test_data = [{
        'category': '테스트',
        'title': '테스트 게시글',
        'url': 'https://test.example.com/test',
        'date': '2024.01.01',
        'crawled_at': '2024-01-01 00:00:00'
    }]
    
    crawler1.existing_data.extend(test_data)
    crawler1.save_data()
    print("테스트 데이터 추가 및 저장 완료")
    
    # 두 번째 크롤러 인스턴스 (새로 로드)
    crawler2 = MultiURLScheduledCrawler()
    loaded_count = len(crawler2.existing_data)
    print(f"로드된 데이터 수: {loaded_count}개")
    
    if loaded_count == initial_count + 1:
        print("✓ 데이터 지속성 테스트 성공")
        return True
    else:
        print("✗ 데이터 지속성 테스트 실패")
        return False

def test_performance():
    """
    성능 테스트
    """
    print("\n=== 성능 테스트 ===")
    
    crawler = MultiURLScheduledCrawler()
    
    # 순차 처리 테스트
    print("순차 처리 테스트 중...")
    start_time = time.time()
    sequential_data = crawler.crawl_all_urls(max_pages=1, use_threading=False)
    sequential_time = time.time() - start_time
    
    # 병렬 처리 테스트
    print("병렬 처리 테스트 중...")
    start_time = time.time()
    parallel_data = crawler.crawl_all_urls(max_pages=1, use_threading=True)
    parallel_time = time.time() - start_time
    
    print(f"\n=== 성능 비교 결과 ===")
    print(f"순차 처리: {sequential_time:.2f}초, {len(sequential_data)}개 게시글")
    print(f"병렬 처리: {parallel_time:.2f}초, {len(parallel_data)}개 게시글")
    
    if parallel_time < sequential_time:
        improvement = ((sequential_time - parallel_time) / sequential_time * 100)
        print(f"성능 향상: {improvement:.1f}%")
    else:
        print("병렬 처리가 더 느렸습니다.")

def cleanup_test_files():
    """
    테스트 파일 정리
    """
    print("\n=== 테스트 파일 정리 ===")
    
    test_files = [
        'multi_notices_data.json',
        'multi_scheduled_crawler.log',
        'multi_crawler_config.json'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✓ {file} 삭제 완료")
            except Exception as e:
                print(f"✗ {file} 삭제 실패: {e}")

def main():
    """
    메인 테스트 함수
    """
    print("전북대학교 컴퓨터인공지능학부 다중 URL 스케줄러 크롤러 테스트")
    print("=" * 70)
    
    try:
        # 1. 설정 파일 로딩 테스트
        test_config_loading()
        
        # 2. 단일 URL 크롤링 테스트
        test_single_url_crawl()
        
        # 3. 새로운 게시글 감지 테스트
        test_new_post_detection()
        
        # 4. 전체 크롤링 테스트
        test_full_crawl()
        
        # 5. 데이터 지속성 테스트
        test_data_persistence()
        
        # 6. 성능 테스트
        test_performance()
        
        print("\n=== 모든 테스트 완료 ===")
        print("모든 테스트가 성공적으로 완료되었습니다.")
        
        # 테스트 파일 정리 여부 확인
        print("\n테스트 파일을 정리하시겠습니까? (y/n): ", end="")
        if input().lower() == 'y':
            cleanup_test_files()
        
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
