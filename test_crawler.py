#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
크롤러 테스트 스크립트
"""

from crawler import JBNUCrawler

def test_crawler():
    """크롤러 기본 기능 테스트"""
    print("전북대학교 컴퓨터인공지능학부 크롤러 테스트")
    print("=" * 50)
    
    crawler = JBNUCrawler()
    
    # 첫 페이지 공지사항 목록만 테스트
    print("1. 공지사항 목록 크롤링 테스트...")
    notices = crawler.get_notice_list(page=1)
    
    if notices:
        print(f"✓ 성공: {len(notices)}개 공지사항 수집")
        print("\n수집된 공지사항 샘플:")
        for i, notice in enumerate(notices[:3], 1):
            print(f"  {i}. [{notice['date']}] {notice['title']}")
        
        # JSON으로 저장 테스트
        print("\n2. JSON 저장 테스트...")
        crawler.save_to_json(notices, "test_notices.json")
        
        # CSV로 저장 테스트
        print("\n3. CSV 저장 테스트...")
        crawler.save_to_csv(notices, "test_notices.csv")
        
        print("\n✓ 모든 테스트 완료!")
        
    else:
        print("✗ 공지사항을 수집할 수 없습니다.")

if __name__ == "__main__":
    test_crawler()
