#!/usr/bin/env python3
"""
로컬 JSON 데이터를 Firebase에 동기화하는 스크립트
"""
import json
import os
import sys
import asyncio
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_service import FirebaseService

async def sync_to_firebase():
    """로컬 JSON 데이터를 Firebase에 동기화"""
    
    print("🔄 Firebase 동기화 시작...")
    
    # Firebase 서비스 초기화
    firebase_service = FirebaseService()
    
    if not firebase_service.is_initialized():
        print("❌ Firebase 초기화 실패")
        print("📋 설정 확인 사항:")
        print("   1. .env 파일이 올바르게 설정되었는지 확인")
        print("   2. firebase-service-account.json 파일이 있는지 확인")
        print("   3. Firebase 프로젝트 ID가 정확한지 확인")
        return False
    
    print("✅ Firebase 연결 성공")
    
    # 로컬 JSON 파일 읽기
    json_file = "notices_data.json"
    if not os.path.exists(json_file):
        print(f"❌ {json_file} 파일을 찾을 수 없습니다")
        return False
    
    print(f"📄 {json_file} 파일 읽는 중...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            notices_data = json.load(f)
        
        print(f"📊 총 {len(notices_data)}개의 공지사항 발견")
        
        # Firebase에 배치 저장
        print("🚀 Firebase에 데이터 업로드 중...")
        result = await firebase_service.save_notices_batch(notices_data)
        
        print("✅ 동기화 완료!")
        print(f"   - 성공: {result['success']}개")
        print(f"   - 실패: {result['failed']}개")
        
        if result['failed'] > 0:
            print("⚠️  일부 데이터 저장에 실패했습니다")
            print("   - Firebase 권한 확인")
            print("   - 네트워크 연결 확인")
        
        # Firebase 통계 조회
        print("\n📈 Firebase 통계:")
        stats = await firebase_service.get_firebase_stats()
        print(f"   - 총 문서 수: {stats.get('total_documents', 0)}")
        print(f"   - 최근 업데이트: {stats.get('last_updated', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 동기화 중 오류 발생: {e}")
        return False

async def main():
    """메인 함수"""
    print("=" * 50)
    print("🔥 Firebase 동기화 도구")
    print("=" * 50)
    
    success = await sync_to_firebase()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 동기화가 성공적으로 완료되었습니다!")
        print("📱 Firebase Console에서 데이터를 확인하세요:")
        print("   https://console.firebase.google.com")
    else:
        print("❌ 동기화에 실패했습니다.")
        print("📋 위의 오류 메시지를 확인하고 설정을 점검하세요.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())

