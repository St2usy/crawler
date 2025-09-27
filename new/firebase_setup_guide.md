# Firebase 설정 가이드

이 가이드는 공지사항 크롤러 API 서버에서 Firebase를 사용하기 위한 설정 방법을 설명합니다.

## 1. Firebase 프로젝트 생성

1. [Firebase 콘솔](https://console.firebase.google.com/)에 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: `notice-crawler`)
4. Google Analytics 설정 (선택사항)
5. 프로젝트 생성 완료

## 2. Firestore 데이터베이스 설정

1. Firebase 콘솔에서 생성한 프로젝트 선택
2. 왼쪽 메뉴에서 "Firestore Database" 클릭
3. "데이터베이스 만들기" 클릭
4. 보안 규칙 설정:
   - **테스트 모드**: 개발 중에 사용 (모든 읽기/쓰기 허용)
   - **프로덕션 모드**: 운영 환경에서 사용 (보안 규칙 설정 필요)

### 테스트 모드 보안 규칙 (개발용)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

### 프로덕션 모드 보안 규칙 (운영용)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /notices/{noticeId} {
      allow read: if true;
      allow write: if false; // 서버에서만 쓰기 허용
    }
  }
}
```

## 3. 서비스 계정 키 생성

1. Firebase 콘솔에서 프로젝트 설정 (톱니바퀴 아이콘) 클릭
2. "서비스 계정" 탭 선택
3. "새 비공개 키 생성" 클릭
4. JSON 파일 다운로드 (안전한 곳에 보관)

## 4. 환경 변수 설정

다운로드한 JSON 파일의 내용을 사용하여 `.env` 파일을 생성합니다:

```bash
# .env 파일 생성
cp env_example.txt .env
```

`.env` 파일을 편집하여 Firebase 설정 정보를 입력:

```env
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

### 중요 사항:
- `FIREBASE_PRIVATE_KEY`는 개행 문자(`\n`)를 포함해야 합니다
- 모든 값은 따옴표로 감싸지 마세요 (이미 JSON에서 따옴표 처리됨)
- `.env` 파일은 절대 Git에 커밋하지 마세요

## 5. 서비스 계정 JSON 파일 직접 사용 (대안)

환경 변수 대신 JSON 파일을 직접 사용할 수도 있습니다:

1. 다운로드한 JSON 파일을 `firebase-service-account.json`으로 이름 변경
2. `firebase_service.py`에서 환경 변수 대신 JSON 파일 로드하도록 수정

```python
# firebase_service.py 수정 예시
def _initialize_firebase(self):
    if os.getenv('ENABLE_FIREBASE_SYNC', 'false').lower() != 'true':
        return
    
    # JSON 파일 사용
    if os.path.exists('firebase-service-account.json'):
        cred = credentials.Certificate('firebase-service-account.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.initialized = True
    else:
        # 환경 변수 사용 (기존 방식)
        # ... 기존 코드 ...
```

## 6. 연결 테스트

서버 실행 후 다음 API를 호출하여 Firebase 연결을 테스트합니다:

```bash
# Firebase 연결 테스트
curl http://localhost:8000/firebase/test

# Firebase 통계 조회
curl http://localhost:8000/firebase/stats

# 로컬 데이터를 Firebase에 동기화
curl -X POST http://localhost:8000/firebase/sync
```

## 7. 스케줄러 설정

5분 단위로 자동 크롤링을 시작하려면:

```bash
# 스케줄러 시작
curl -X POST http://localhost:8000/scheduler/start

# 스케줄러 상태 확인
curl http://localhost:8000/scheduler/status

# 크롤링 간격 변경 (예: 10분)
curl -X PUT "http://localhost:8000/scheduler/interval?minutes=10"
```

## 8. 데이터 구조

Firebase에 저장되는 공지사항 데이터 구조:

```json
{
  "category": "학과소식",
  "number": "1234",
  "title": "공지사항 제목",
  "author": "작성자",
  "date": "2024.01.15",
  "attachments": "첨부파일 정보",
  "views": "조회수",
  "url": "https://csai.jbnu.ac.kr/...",
  "content": "공지사항 내용",
  "content_html": "<div>HTML 원문</div>",
  "image_urls": ["이미지 URL 목록"],
  "crawled_at": "2024-01-15 10:30:00",
  "firebase_created_at": "2024-01-15T10:30:00.000Z",
  "firebase_updated_at": "2024-01-15T10:30:00.000Z"
}
```

## 9. 문제 해결

### Firebase 연결 실패
- 환경 변수가 올바르게 설정되었는지 확인
- `FIREBASE_PRIVATE_KEY`의 개행 문자 확인
- Firebase 프로젝트 ID가 정확한지 확인

### 권한 오류
- Firestore 보안 규칙 확인
- 서비스 계정 권한 확인

### 데이터 저장 실패
- Firestore 데이터베이스가 생성되었는지 확인
- 컬렉션 이름이 올바른지 확인 (`notices`)

## 10. 보안 고려사항

1. **환경 변수 보호**: `.env` 파일을 Git에 커밋하지 마세요
2. **서비스 계정 키 보안**: JSON 키 파일을 안전한 곳에 보관
3. **Firestore 보안 규칙**: 프로덕션에서는 적절한 보안 규칙 설정
4. **네트워크 보안**: 필요한 경우 VPC나 방화벽 설정

## 11. 모니터링

Firebase 콘솔에서 다음을 모니터링할 수 있습니다:
- 데이터베이스 사용량
- 읽기/쓰기 작업 수
- 에러 로그
- 성능 메트릭

