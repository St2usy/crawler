# Firebase 환경변수 설정 가이드

## 🔥 Firebase 환경변수 설정 방법

### 방법 1: .env 파일 사용 (권장)

#### 1단계: Firebase 프로젝트 설정

1. **Firebase Console** (https://console.firebase.google.com) 접속
2. **프로젝트 선택** 또는 새 프로젝트 생성
3. **프로젝트 설정** (⚙️ 아이콘) 클릭
4. **서비스 계정** 탭 선택
5. **새 비공개 키 생성** 버튼 클릭
6. JSON 파일 다운로드

#### 2단계: .env 파일 생성

`new` 폴더에 `.env` 파일을 생성하고 다음 내용을 추가:

```bash
# Firebase 프로젝트 ID (Firebase Console에서 확인)
FIREBASE_PROJECT_ID=your-project-id

# 서비스 계정 키 정보 (다운로드한 JSON 파일에서 복사)
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project-id.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com

# 크롤링 설정
CRAWL_INTERVAL_MINUTES=5
FIREBASE_COLLECTION_NAME=notices
ENABLE_FIREBASE_SYNC=true
```

#### 3단계: 실제 값으로 수정

다운로드한 JSON 파일을 열어서 각 값을 복사:

```json
{
  "type": "service_account",
  "project_id": "your-actual-project-id",          // FIREBASE_PROJECT_ID
  "private_key_id": "abc123...",                   // FIREBASE_PRIVATE_KEY_ID
  "private_key": "-----BEGIN PRIVATE KEY-----\n...", // FIREBASE_PRIVATE_KEY
  "client_email": "firebase-adminsdk-...@...",     // FIREBASE_CLIENT_EMAIL
  "client_id": "123456789...",                     // FIREBASE_CLIENT_ID
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### 방법 2: 서비스 계정 JSON 파일 사용

#### 1단계: JSON 파일 저장

1. Firebase Console에서 다운로드한 JSON 파일을 `firebase-service-account.json`으로 이름 변경
2. `new` 폴더에 저장

#### 2단계: .env 파일 생성 (최소 설정)

```bash
# 최소 환경변수 설정
FIREBASE_PROJECT_ID=your-project-id
ENABLE_FIREBASE_SYNC=true
FIREBASE_COLLECTION_NAME=notices
CRAWL_INTERVAL_MINUTES=5
```

## 🚀 설정 확인 및 테스트

### 1. 서버 재시작

```bash
# 환경변수 적용을 위해 서버 재시작
python run.py
```

### 2. Firebase 연결 테스트

```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/firebase/test" -UseBasicParsing

# 또는 브라우저에서
http://localhost:8000/firebase/test
```

### 3. 환경변수 확인

```bash
# PowerShell에서 환경변수 확인
Get-ChildItem Env: | Where-Object {$_.Name -like "FIREBASE_*"}
```

## 🔧 문제 해결

### Firebase 초기화 실패

**원인**: 환경변수 설정 오류
**해결방법**:
1. .env 파일의 모든 값이 올바른지 확인
2. 따옴표와 이스케이프 문자 확인
3. 프로젝트 ID가 정확한지 확인

### 권한 오류

**원인**: 서비스 계정 권한 부족
**해결방법**:
1. Firebase Console → IAM 및 관리자 → 서비스 계정
2. 해당 서비스 계정에 Firestore 권한 부여
3. 프로젝트 편집자 또는 Firestore 관리자 역할 할당

### 네트워크 오류

**원인**: 방화벽 또는 네트워크 설정
**해결방법**:
1. 방화벽에서 Firebase 도메인 허용
2. 프록시 설정 확인
3. 인터넷 연결 상태 확인

## 📋 체크리스트

- [ ] Firebase 프로젝트 생성 완료
- [ ] Firestore Database 활성화
- [ ] 서비스 계정 키 생성 및 다운로드
- [ ] .env 파일 생성 및 환경변수 설정
- [ ] 서버 재시작
- [ ] Firebase 연결 테스트 성공
- [ ] 데이터 동기화 테스트

## 🎯 다음 단계

환경변수 설정 완료 후:

1. **데이터 동기화**: `POST /firebase/sync`
2. **통계 확인**: `GET /firebase/stats`
3. **자동 크롤링**: `POST /scheduler/start`
