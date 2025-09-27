# Firebase 동기화 가이드

## 🔥 Firebase 설정 방법

### 방법 1: 환경 변수 사용 (.env 파일)

1. `new` 폴더에 `.env` 파일 생성
2. 다음 내용을 실제 Firebase 값으로 수정:

```bash
# Firebase 설정
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-client-email@your-project-id.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-client-email%40your-project-id.iam.gserviceaccount.com

# 크롤링 설정
CRAWL_INTERVAL_MINUTES=5
FIREBASE_COLLECTION_NAME=notices
ENABLE_FIREBASE_SYNC=true
```

### 방법 2: 서비스 계정 JSON 파일 사용

1. Firebase Console에서 서비스 계정 키 JSON 파일 다운로드
2. 파일명을 `firebase-service-account.json`으로 변경
3. `new` 폴더에 저장

## 🚀 동기화 실행 방법

### 1. 서버 재시작 (환경 변수 적용)
```bash
# 서버 중지 후 재시작
python run.py
```

### 2. Firebase 연결 테스트
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/firebase/test" -UseBasicParsing

# 또는 브라우저에서
http://localhost:8000/firebase/test
```

### 3. 로컬 데이터 동기화
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/firebase/sync" -Method POST -UseBasicParsing

# 또는 브라우저에서
http://localhost:8000/docs
# POST /firebase/sync 실행
```

### 4. Firebase 통계 확인
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/firebase/stats" -UseBasicParsing
```

## 📊 동기화 결과 확인

### Firebase Console에서 확인
1. https://console.firebase.google.com 접속
2. 프로젝트 선택
3. Firestore Database → 데이터 탭
4. `notices` 컬렉션에서 데이터 확인

### API로 확인
```bash
# 전체 공지사항 조회
Invoke-WebRequest -Uri "http://localhost:8000/notices?limit=5" -UseBasicParsing

# 카테고리별 요약
Invoke-WebRequest -Uri "http://localhost:8000/summary" -UseBasicParsing
```

## 🔧 문제 해결

### Firebase 초기화 오류
- 환경 변수 또는 서비스 계정 파일 확인
- Firebase 프로젝트 ID 정확성 확인
- Firestore Database 활성화 확인

### 권한 오류
- 서비스 계정에 Firestore 권한 확인
- 프로젝트 설정에서 API 활성화 확인

### 네트워크 오류
- 방화벽 설정 확인
- 인터넷 연결 상태 확인
