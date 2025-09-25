# 다중 URL 스케줄러 크롤러

전북대학교 컴퓨터인공지능학부의 5개 공지사항 카테고리를 동시에 크롤링하고, 새로운 글만 추적하여 한 파일에 저장하는 스케줄러입니다.

## 주요 기능

- **다중 URL 동시 크롤링**: 5개 카테고리의 공지사항을 병렬로 크롤링
- **새로운 글 추적**: 기존 데이터와 비교하여 새로운 게시글만 감지
- **스케줄러**: 설정된 간격으로 자동 크롤링 실행
- **통합 데이터 관리**: 모든 카테고리의 데이터를 하나의 파일에 저장
- **성능 최적화**: 병렬 처리로 크롤링 속도 향상

## 크롤링 대상

1. **학과소식** - https://csai.jbnu.ac.kr/csai/29105/subview.do
2. **일반공지** - https://csai.jbnu.ac.kr/csai/29106/subview.do
3. **학사공지** - https://csai.jbnu.ac.kr/csai/29107/subview.do
4. **사업단공지** - https://csai.jbnu.ac.kr/csai/31501/subview.do
5. **취업정보** - https://csai.jbnu.ac.kr/csai/29108/subview.do

## 설치 및 실행

### 1. 필요한 패키지 설치

```bash
pip install requests beautifulsoup4 schedule
```

### 2. 기본 실행

```bash
# 스케줄러 시작 (30분마다 자동 실행)
python multi_url_scheduled_crawler.py

# 한 번만 실행 (새로운 글만 확인)
python multi_url_scheduled_crawler.py --once

# 전체 크롤링 (기존 데이터 무시하고 모든 글 수집)
python multi_url_scheduled_crawler.py --full

# 요약 정보 출력
python multi_url_scheduled_crawler.py --summary
```

### 3. 테스트 실행

```bash
python test_multi_scheduled_crawler.py
```

## 설정 파일

`multi_crawler_config.json` 파일에서 설정을 변경할 수 있습니다:

```json
{
  "base_url": "https://csai.jbnu.ac.kr",
  "data_file": "multi_notices_data.json",
  "check_interval_minutes": 30,
  "max_pages": 2,
  "target_urls": {
    "https://csai.jbnu.ac.kr/csai/29105/subview.do": "학과소식",
    "https://csai.jbnu.ac.kr/csai/29106/subview.do": "일반공지",
    "https://csai.jbnu.ac.kr/csai/29107/subview.do": "학사공지",
    "https://csai.jbnu.ac.kr/csai/31501/subview.do": "사업단공지",
    "https://csai.jbnu.ac.kr/csai/29108/subview.do": "취업정보"
  },
  "notification": {
    "enabled": false,
    "webhook_url": "",
    "message_template": "새로운 공지사항이 등록되었습니다: [{category}] {title}"
  }
}
```

### 설정 옵션

- `check_interval_minutes`: 크롤링 간격 (분)
- `max_pages`: 각 카테고리당 크롤링할 최대 페이지 수
- `data_file`: 데이터 저장 파일명
- `target_urls`: 크롤링할 URL과 카테고리 매핑
- `notification`: 알림 설정 (웹훅 등)

## 데이터 구조

수집된 데이터는 JSON 형태로 저장되며, 각 게시글은 다음과 같은 구조를 가집니다:

```json
{
  "category": "학과소식",
  "number": "70",
  "title": "허완·허민·박현찬 교수팀 – 학부생 논문경진대회 수상 (2025 한국정보과학회)",
  "author": "컴퓨터인공지능학부",
  "date": "2025.08.25",
  "attachments": "0",
  "views": "388",
  "url": "https://csai.jbnu.ac.kr/csai/29105/subview.do?enc=Zm5jdDFfQ2hhcmFjdGVyXzQ2MjEw",
  "content": "게시글 상세 내용...",
  "crawled_at": "2024-09-25 17:05:21"
}
```

## 로그 파일

- `multi_scheduled_crawler.log`: 크롤링 과정의 상세 로그
- 콘솔 출력: 실시간 진행 상황

## 성능 특징

- **병렬 처리**: 3개의 워커 스레드로 동시 크롤링
- **새로운 글만 추적**: URL 기준으로 중복 제거
- **서버 부하 방지**: 요청 간 딜레이 설정
- **오류 처리**: 개별 URL 실패 시에도 다른 URL 계속 처리

## 사용 예시

### 1. 스케줄러로 실행

```bash
# 백그라운드에서 실행
nohup python multi_url_scheduled_crawler.py > output.log 2>&1 &

# 실행 중인 프로세스 확인
ps aux | grep multi_url_scheduled_crawler

# 프로세스 종료
kill <PID>
```

### 2. 새로운 글 확인

```bash
# 새로운 글만 확인
python multi_url_scheduled_crawler.py --once

# 결과 예시:
# 새로운 게시글 3개 발견:
# - [학과소식] [2024.09.25] 새로운 공지사항 1
# - [학사공지] [2024.09.25] 새로운 공지사항 2
# - [취업정보] [2024.09.25] 새로운 공지사항 3
```

### 3. 데이터 요약 확인

```bash
python multi_url_scheduled_crawler.py --summary

# 결과 예시:
# === 크롤링 결과 요약 ===
# 총 게시글 수: 150개
# - 학과소식: 30개
# - 일반공지: 25개
# - 학사공지: 40개
# - 사업단공지: 20개
# - 취업정보: 35개
```

## 문제 해결

### 1. 크롤링 실패 시

- 로그 파일 확인: `multi_scheduled_crawler.log`
- 네트워크 연결 상태 확인
- 서버 응답 시간 확인

### 2. 데이터 중복 시

- `--full` 옵션으로 전체 크롤링 실행
- 기존 데이터 파일 삭제 후 재시작

### 3. 메모리 사용량 증가 시

- `max_pages` 설정을 줄여서 크롤링 범위 제한
- 주기적으로 오래된 데이터 정리

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다. 상업적 사용 시 해당 웹사이트의 이용약관을 확인하시기 바랍니다.
