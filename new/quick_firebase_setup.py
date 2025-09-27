#!/usr/bin/env python3
"""
Firebase 빠른 설정 스크립트
"""
import os
import sys

def create_minimal_env():
    """최소 환경변수 설정"""
    print("🔥 Firebase 최소 설정 생성 중...")
    
    # 사용자 입력 받기
    project_id = input("📋 Firebase 프로젝트 ID를 입력하세요: ").strip()
    
    if not project_id:
        print("❌ 프로젝트 ID가 필요합니다")
        return False
    
    env_content = f"""# Firebase 최소 설정
FIREBASE_PROJECT_ID={project_id}
ENABLE_FIREBASE_SYNC=true
FIREBASE_COLLECTION_NAME=notices
CRAWL_INTERVAL_MINUTES=5
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env 파일이 생성되었습니다")
        print("📝 다음 단계:")
        print("   1. Firebase Console에서 서비스 계정 키 JSON 파일 다운로드")
        print("   2. 파일명을 'firebase-service-account.json'으로 변경")
        print("   3. new 폴더에 저장")
        print("   4. 서버 재시작")
        return True
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("="*40)
    print("⚡ Firebase 빠른 설정")
    print("="*40)
    
    if os.path.exists('.env'):
        response = input("📁 .env 파일이 이미 있습니다. 덮어쓰시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("❌ 설정이 취소되었습니다")
            return
    
    create_minimal_env()

if __name__ == "__main__":
    main()
