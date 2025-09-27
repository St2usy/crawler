# 공지사항 크롤러 API 서버

전북대학교 컴퓨터공학부 공지사항을 크롤링하고 React 프로젝트와 API 통신을 위한 FastAPI 서버입니다.

## 기능

- 🔍 **공지사항 크롤링**: 5개 카테고리의 공지사항을 자동으로 크롤링
- 📊 **API 제공**: RESTful API를 통한 공지사항 데이터 제공
- 🔄 **실시간 업데이트**: 새로운 공지사항 자동 감지 및 저장
- 🔍 **검색 기능**: 제목 및 내용 기반 검색
- 📱 **React 연동**: CORS 설정으로 React 프로젝트와 연동 가능
- ⏰ **스케줄링**: 5분 단위 자동 크롤링 (간격 조정 가능)
- 🔥 **Firebase 연동**: 크롤링된 데이터를 Firebase Firestore에 자동 저장
- 📈 **통계 및 모니터링**: Firebase 데이터 통계 및 크롤링 상태 모니터링

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 서버 실행

#### Windows
```bash
run.bat
```

#### Linux/Mac
```bash
python run.py
```

#### 직접 실행
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 확인

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 기본 정보
- `GET /` - API 루트 정보
- `GET /health` - 헬스 체크

### 공지사항 조회
- `GET /notices` - 공지사항 목록 조회
  - Query Parameters:
    - `category` (optional): 카테고리 필터
    - `limit` (optional): 결과 수 제한
    - `offset` (optional): 시작 위치 (기본값: 0)
- `GET /notices/{notice_id}` - 특정 공지사항 상세 조회
- `GET /latest` - 최신 공지사항 조회
  - Query Parameters:
    - `limit` (optional): 결과 수 제한 (기본값: 10)

### 카테고리 및 요약
- `GET /categories` - 카테고리 목록 조회
- `GET /summary` - 카테고리별 요약 정보 조회

### 검색
- `GET /search` - 공지사항 검색
  - Query Parameters:
    - `query` (required): 검색어
    - `category` (optional): 카테고리 필터
    - `limit` (optional): 결과 수 제한 (기본값: 20)

### 크롤링 관리
- `POST /crawl` - 새로운 공지사항 크롤링 실행
- `POST /crawl/full` - 전체 크롤링 실행
- `POST /crawl/now` - 즉시 크롤링 실행
- `GET /crawl/status` - 크롤링 상태 조회

### 스케줄러 관리
- `POST /scheduler/start` - 스케줄러 시작
- `POST /scheduler/stop` - 스케줄러 중지
- `GET /scheduler/status` - 스케줄러 상태 조회
- `PUT /scheduler/interval` - 크롤링 간격 변경
  - Query Parameters:
    - `minutes` (required): 새로운 간격 (분)

### Firebase 관리
- `GET /firebase/test` - Firebase 연결 테스트
- `GET /firebase/stats` - Firebase 통계 정보 조회
- `POST /firebase/sync` - 로컬 데이터를 Firebase에 동기화

## React 연동 예시

### 1. API 호출 함수

```javascript
// api.js
const API_BASE_URL = 'http://localhost:8000';

export const api = {
  // 공지사항 목록 조회
  getNotices: async (category = null, limit = null, offset = 0) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);
    
    const response = await fetch(`${API_BASE_URL}/notices?${params}`);
    return response.json();
  },

  // 공지사항 상세 조회
  getNotice: async (noticeId) => {
    const response = await fetch(`${API_BASE_URL}/notices/${noticeId}`);
    return response.json();
  },

  // 검색
  searchNotices: async (query, category = null, limit = 20) => {
    const params = new URLSearchParams({ query, limit });
    if (category) params.append('category', category);
    
    const response = await fetch(`${API_BASE_URL}/search?${params}`);
    return response.json();
  },

  // 카테고리 목록
  getCategories: async () => {
    const response = await fetch(`${API_BASE_URL}/categories`);
    return response.json();
  },

  // 요약 정보
  getSummary: async () => {
    const response = await fetch(`${API_BASE_URL}/summary`);
    return response.json();
  },

  // 크롤링 실행
  startCrawl: async () => {
    const response = await fetch(`${API_BASE_URL}/crawl`, { method: 'POST' });
    return response.json();
  },

  // 크롤링 상태
  getCrawlStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/crawl/status`);
    return response.json();
  }
};
```

### 2. React 컴포넌트 예시

```jsx
// NoticeList.jsx
import React, { useState, useEffect } from 'react';
import { api } from './api';

const NoticeList = () => {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    loadData();
  }, [category]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [noticesData, categoriesData] = await Promise.all([
        api.getNotices(category || null, 20),
        api.getCategories()
      ]);
      setNotices(noticesData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      loadData();
      return;
    }
    
    setLoading(true);
    try {
      const result = await api.searchNotices(query, category || null);
      setNotices(result.results);
    } catch (error) {
      console.error('검색 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>로딩 중...</div>;

  return (
    <div>
      <h1>공지사항</h1>
      
      {/* 카테고리 필터 */}
      <select 
        value={category} 
        onChange={(e) => setCategory(e.target.value)}
      >
        <option value="">전체</option>
        {categories.map(cat => (
          <option key={cat} value={cat}>{cat}</option>
        ))}
      </select>

      {/* 검색 */}
      <input
        type="text"
        placeholder="검색어 입력..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSearch(e.target.value);
          }
        }}
      />

      {/* 공지사항 목록 */}
      <div>
        {notices.map(notice => (
          <div key={notice.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
            <h3>{notice.title}</h3>
            <p>카테고리: {notice.category}</p>
            <p>작성자: {notice.author}</p>
            <p>날짜: {notice.date}</p>
            <p>조회수: {notice.views}</p>
            {notice.attachments && <p>첨부파일: {notice.attachments}</p>}
            <a href={notice.url} target="_blank" rel="noopener noreferrer">
              원문 보기
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NoticeList;
```

## Firebase 설정

Firebase 연동을 위해서는 별도의 설정이 필요합니다. 자세한 설정 방법은 [Firebase 설정 가이드](firebase_setup_guide.md)를 참조하세요.

### 환경 변수 설정 (.env)
```env
# Firebase 설정
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-client-email@your-project-id.iam.gserviceaccount.com
# ... 기타 Firebase 설정

# 크롤링 설정
CRAWL_INTERVAL_MINUTES=5
FIREBASE_COLLECTION_NAME=notices
ENABLE_FIREBASE_SYNC=true
```

## 설정

### 크롤링 설정 (crawler_config.json)

```json
{
  "base_url": "https://csai.jbnu.ac.kr",
  "data_file": "notices_data.json",
  "max_pages": 2,
  "target_urls": {
    "https://csai.jbnu.ac.kr/csai/29105/subview.do": "학과소식",
    "https://csai.jbnu.ac.kr/csai/29106/subview.do": "일반공지",
    "https://csai.jbnu.ac.kr/csai/29107/subview.do": "학사공지",
    "https://csai.jbnu.ac.kr/csai/31501/subview.do": "사업단공지",
    "https://csai.jbnu.ac.kr/csai/29108/subview.do": "취업정보"
  }
}
```

## 데이터 구조

### NoticeResponse
```json
{
  "id": "string",
  "category": "string",
  "number": "string",
  "title": "string",
  "author": "string",
  "date": "string",
  "attachments": "string",
  "views": "string",
  "url": "string",
  "content": "string",
  "content_html": "string",
  "image_urls": ["string"],
  "crawled_at": "string"
}
```

## 로그

서버 실행 시 `multi_scheduled_crawler.log` 파일에 크롤링 로그가 저장됩니다.

## 자동 크롤링 시작

Firebase 연동 후 5분 단위 자동 크롤링을 시작하려면:

```bash
# 스케줄러 시작
curl -X POST http://localhost:8000/scheduler/start

# 상태 확인
curl http://localhost:8000/scheduler/status

# Firebase 통계 확인
curl http://localhost:8000/firebase/stats
```

## 문제 해결

1. **CORS 오류**: React 앱의 주소가 `app.py`의 `allow_origins`에 포함되어 있는지 확인
2. **크롤링 실패**: 네트워크 연결 및 대상 사이트 접근 가능 여부 확인
3. **데이터 로드 실패**: `notices_data.json` 파일 권한 및 형식 확인
4. **Firebase 연결 실패**: 환경 변수 설정 및 Firebase 프로젝트 설정 확인
5. **스케줄러 오류**: 로그 파일 확인 및 Firebase 권한 설정 확인

## 라이선스

MIT License
