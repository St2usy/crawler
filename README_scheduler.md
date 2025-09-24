# 주기적 크롤링 스케줄러

특정 게시판의 새로운 게시글을 주기적으로 확인하고 크롤링하는 스케줄러입니다.

## 주요 기능

- 🔄 **주기적 크롤링**: 설정된 간격으로 자동 크롤링
- 🆕 **새 게시글 감지**: 기존 데이터와 비교하여 새로운 게시글만 추출
- 💾 **JSON 저장**: 모든 데이터를 JSON 형식으로 저장
- ⚙️ **설정 가능**: 간격, 대상 URL, 저장 파일 등 커스터마이징 가능
- 📝 **로깅**: 모든 활동을 로그 파일로 기록
- 🔔 **알림 기능**: 새로운 게시글 발견 시 알림 발송 (선택사항)

## 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 설정 파일 수정
`crawler_config.json` 파일을 수정하여 원하는 설정을 적용하세요:

```json
{
  "base_url": "https://csai.jbnu.ac.kr",
  "target_url": "https://csai.jbnu.ac.kr/csai/29107/subview.do",
  "data_file": "notices_data.json",
  "check_interval_minutes": 30,
  "max_pages": 2,
  "notification": {
    "enabled": false,
    "webhook_url": "",
    "message_template": "새로운 공지사항이 등록되었습니다: {title}"
  }
}
```

### 설정 옵션 설명

- `base_url`: 웹사이트 기본 URL
- `target_url`: 크롤링할 게시판 URL
- `data_file`: 데이터를 저장할 JSON 파일명
- `check_interval_minutes`: 크롤링 간격 (분 단위)
- `max_pages`: 최대 확인할 페이지 수
- `notification`: 알림 설정
  - `enabled`: 알림 활성화 여부
  - `webhook_url`: 웹훅 URL (Discord, Slack 등)
  - `message_template`: 알림 메시지 템플릿

## 사용법

### 1. 스케줄러 실행 (지속적 실행)
```bash
python scheduled_crawler.py
```

### 2. 한 번만 실행 (테스트용)
```bash
python scheduled_crawler.py --once
```

## 출력 파일

### 1. notices_data.json
크롤링된 모든 게시글 데이터가 저장됩니다:
```json
[
  {
    "number": "일반공지",
    "title": "[ 일반공지 ] 게시글 제목",
    "author": "작성자",
    "date": "2025.09.22",
    "attachments": "1",
    "views": "136",
    "url": "https://example.com/post/123",
    "content": "게시글 내용...",
    "crawled_at": "2025-01-24 14:30:00"
  }
]
```

### 2. crawler.log
크롤링 활동 로그가 저장됩니다:
```
2025-01-24 14:30:00,123 - INFO - 스케줄러 초기화 완료 - 체크 간격: 30분, 데이터 파일: notices_data.json
2025-01-24 14:30:00,456 - INFO - 새로운 게시글 확인 시작...
2025-01-24 14:30:05,789 - INFO - 새 게시글 발견: [ 일반공지 ] 새로운 게시글 제목...
```

## 동작 원리

1. **초기화**: 기존 데이터 파일(`notices_data.json`)을 로드
2. **크롤링**: 설정된 URL에서 게시글 목록 가져오기
3. **새 게시글 감지**: 기존 데이터와 URL 비교하여 새로운 게시글 식별
4. **상세 내용 수집**: 새로운 게시글의 상세 내용 크롤링
5. **데이터 저장**: 새로운 게시글을 기존 데이터 앞에 추가하여 저장
6. **알림 발송**: 설정된 경우 새로운 게시글에 대한 알림 발송
7. **대기**: 설정된 간격만큼 대기 후 반복

## 주의사항

- 서버 부하를 방지하기 위해 요청 간 딜레이가 있습니다
- 네트워크 오류 시 재시도 로직이 포함되어 있습니다
- `Ctrl+C`로 스케줄러를 안전하게 종료할 수 있습니다
- 로그 파일은 계속 누적되므로 주기적으로 정리해주세요

## 문제 해결

### 새로운 게시글이 감지되지 않는 경우
1. `crawler_config.json`에서 `target_url`이 올바른지 확인
2. 웹사이트 구조가 변경되었을 수 있으니 로그 확인
3. `max_pages` 설정을 늘려서 더 많은 페이지 확인

### 크롤링 오류가 발생하는 경우
1. `crawler.log` 파일에서 오류 메시지 확인
2. 네트워크 연결 상태 확인
3. 대상 웹사이트 접근 가능 여부 확인

## 커스터마이징

다른 웹사이트를 크롤링하려면:
1. `crawler_config.json`에서 URL 수정
2. 필요시 `scheduled_crawler.py`의 파싱 로직 수정
3. 테스트 실행 후 정상 작동 확인
