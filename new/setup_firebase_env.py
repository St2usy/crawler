#!/usr/bin/env python3
"""
Firebase 환경변수 설정 도우미 스크립트
"""
import json
import os
import sys
from pathlib import Path

def load_firebase_json():
    """Firebase 서비스 계정 JSON 파일 로드"""
    json_files = [
        'firebase-service-account.json',
        'service-account.json',
        'firebase-adminsdk.json'
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ JSON 파일 발견: {json_file}")
                return data
            except Exception as e:
                print(f"❌ JSON 파일 읽기 실패: {e}")
    
    return None

def create_env_file(firebase_data):
    """환경변수 파일 생성"""
    env_content = f"""# Firebase 환경변수 설정
# 자동 생성됨 - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Firebase 프로젝트 설정
FIREBASE_PROJECT_ID={firebase_data.get('project_id', 'your-project-id')}
FIREBASE_PRIVATE_KEY_ID={firebase_data.get('private_key_id', 'your-private-key-id')}
FIREBASE_PRIVATE_KEY="{firebase_data.get('private_key', 'your-private-key')}"
FIREBASE_CLIENT_EMAIL={firebase_data.get('client_email', 'your-client-email')}
FIREBASE_CLIENT_ID={firebase_data.get('client_id', 'your-client-id')}
FIREBASE_AUTH_URI={firebase_data.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')}
FIREBASE_TOKEN_URI={firebase_data.get('token_uri', 'https://oauth2.googleapis.com/token')}
FIREBASE_AUTH_PROVIDER_X509_CERT_URL={firebase_data.get('auth_provider_x509_cert_url', 'https://www.googleapis.com/oauth2/v1/certs')}
FIREBASE_CLIENT_X509_CERT_URL={firebase_data.get('client_x509_cert_url', 'https://www.googleapis.com/robot/v1/metadata/x509/...')}

# 크롤링 설정
CRAWL_INTERVAL_MINUTES=5
FIREBASE_COLLECTION_NAME=notices
ENABLE_FIREBASE_SYNC=true
"""
    
    env_file = '.env'
    
    # 기존 .env 파일 백업
    if os.path.exists(env_file):
        backup_file = f'{env_file}.backup'
        os.rename(env_file, backup_file)
        print(f"📁 기존 .env 파일을 {backup_file}로 백업했습니다")
    
    # 새 .env 파일 생성
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ {env_file} 파일이 생성되었습니다")
        return True
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {e}")
        return False

def manual_setup():
    """수동 설정 안내"""
    print("\n" + "="*50)
    print("📝 수동 설정 방법")
    print("="*50)
    print("1. Firebase Console (https://console.firebase.google.com) 접속")
    print("2. 프로젝트 선택 → 설정 (⚙️) → 서비스 계정")
    print("3. '새 비공개 키 생성' 클릭하여 JSON 파일 다운로드")
    print("4. 다운로드한 JSON 파일을 'firebase-service-account.json'으로 이름 변경")
    print("5. new 폴더에 저장")
    print("6. 이 스크립트를 다시 실행")
    print("="*50)

def test_firebase_connection():
    """Firebase 연결 테스트"""
    try:
        # .env 파일이 있는지 확인
        if not os.path.exists('.env'):
            print("❌ .env 파일이 없습니다")
            return False
        
        # 환경변수 로드
        from dotenv import load_dotenv
        load_dotenv()
        
        # Firebase 서비스 테스트
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from firebase_service import FirebaseService
        
        firebase_service = FirebaseService()
        if firebase_service.is_initialized():
            print("✅ Firebase 연결 성공!")
            return True
        else:
            print("❌ Firebase 초기화 실패")
            return False
            
    except Exception as e:
        print(f"❌ Firebase 연결 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("="*50)
    print("🔥 Firebase 환경변수 설정 도우미")
    print("="*50)
    
    # 현재 디렉토리 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    print(f"📁 작업 디렉토리: {current_dir}")
    
    # Firebase JSON 파일 확인
    firebase_data = load_firebase_json()
    
    if firebase_data:
        print("📋 Firebase 서비스 계정 정보:")
        print(f"   - 프로젝트 ID: {firebase_data.get('project_id', 'N/A')}")
        print(f"   - 클라이언트 이메일: {firebase_data.get('client_email', 'N/A')}")
        
        # .env 파일 생성
        if create_env_file(firebase_data):
            print("\n🧪 Firebase 연결 테스트 중...")
            if test_firebase_connection():
                print("\n🎉 Firebase 환경변수 설정 완료!")
                print("📱 이제 서버를 재시작하고 Firebase 기능을 사용할 수 있습니다")
            else:
                print("\n⚠️ Firebase 연결에 실패했습니다")
                print("📋 설정을 다시 확인해주세요")
        else:
            print("\n❌ 환경변수 파일 생성에 실패했습니다")
    else:
        print("❌ Firebase 서비스 계정 JSON 파일을 찾을 수 없습니다")
        manual_setup()
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
