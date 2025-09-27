from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import signal
import atexit
from datetime import datetime
from typing import List, Optional
import json
import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler_service import CrawlerService
from models import NoticeResponse, CrawlStatus, CategorySummary

app = FastAPI(
    title="공지사항 크롤러 API",
    description="전북대학교 컴퓨터공학부 공지사항 크롤링 API",
    version="1.0.0"
)

# CORS 설정 (React 연동을 위해)
# 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React 개발 서버 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 크롤러 서비스 인스턴스
crawler_service = CrawlerService()

def cleanup_resources():
    """리소스 정리 함수"""
    try:
        print("\n🔄 서버 종료 중... 리소스를 정리합니다.")
        
        # 스케줄러 중지
        if hasattr(crawler_service, 'scheduler_service'):
            crawler_service.scheduler_service.stop_scheduler()
            print("✅ 스케줄러 중지 완료")
        
        # Firebase 연결 정리
        if hasattr(crawler_service, 'firebase_service'):
            crawler_service.firebase_service.cleanup()
            print("✅ Firebase 연결 정리 완료")
        
        print("✅ 모든 리소스 정리 완료")
        
    except Exception as e:
        print(f"⚠️ 리소스 정리 중 오류: {e}")

# 종료 시 리소스 정리 등록
atexit.register(cleanup_resources)

# 시그널 핸들러 등록 (Ctrl+C, 종료 신호)
def signal_handler(signum, frame):
    print(f"\n🛑 종료 신호 수신 ({signum})")
    cleanup_resources()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # 종료 신호

@app.get("/", response_model=dict)
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "공지사항 크롤러 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/notices", response_model=List[NoticeResponse])
async def get_notices(
    category: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0
):
    """공지사항 목록 조회"""
    try:
        notices = await crawler_service.get_notices(category, limit, offset)
        return notices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notices/{notice_id}", response_model=NoticeResponse)
async def get_notice(notice_id: str):
    """특정 공지사항 상세 조회"""
    try:
        notice = await crawler_service.get_notice_by_id(notice_id)
        if not notice:
            raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")
        return notice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories", response_model=List[str])
async def get_categories():
    """카테고리 목록 조회"""
    try:
        categories = await crawler_service.get_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary", response_model=List[CategorySummary])
async def get_summary():
    """카테고리별 요약 정보 조회"""
    try:
        summary = await crawler_service.get_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl", response_model=CrawlStatus)
async def start_crawl(background_tasks: BackgroundTasks):
    """크롤링 실행 (백그라운드)"""
    try:
        # 백그라운드에서 크롤링 실행
        background_tasks.add_task(crawler_service.crawl_new_posts)
        
        return CrawlStatus(
            status="started",
            message="크롤링이 시작되었습니다",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/full", response_model=CrawlStatus)
async def start_full_crawl(background_tasks: BackgroundTasks):
    """전체 크롤링 실행 (백그라운드)"""
    try:
        # 백그라운드에서 전체 크롤링 실행
        background_tasks.add_task(crawler_service.crawl_all_posts)
        
        return CrawlStatus(
            status="started",
            message="전체 크롤링이 시작되었습니다",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crawl/status", response_model=CrawlStatus)
async def get_crawl_status():
    """크롤링 상태 조회"""
    try:
        status = await crawler_service.get_crawl_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_notices(
    query: str,
    category: Optional[str] = None,
    limit: Optional[int] = 20
):
    """공지사항 검색"""
    try:
        results = await crawler_service.search_notices(query, category, limit)
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest")
async def get_latest_notices(limit: int = 10):
    """최신 공지사항 조회"""
    try:
        notices = await crawler_service.get_latest_notices(limit)
        return notices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/start")
async def start_scheduler():
    """스케줄러 시작"""
    try:
        crawler_service.start_scheduler()
        return {"message": "스케줄러가 시작되었습니다", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/stop")
async def stop_scheduler():
    """스케줄러 중지"""
    try:
        crawler_service.stop_scheduler()
        return {"message": "스케줄러가 중지되었습니다", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        status = crawler_service.get_scheduler_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/scheduler/interval")
async def update_crawl_interval(minutes: int):
    """크롤링 간격 업데이트"""
    try:
        if minutes < 1:
            raise HTTPException(status_code=400, detail="크롤링 간격은 최소 1분 이상이어야 합니다")
        
        success = crawler_service.update_crawl_interval(minutes)
        if success:
            return {"message": f"크롤링 간격이 {minutes}분으로 업데이트되었습니다", "interval": minutes}
        else:
            raise HTTPException(status_code=400, detail="크롤링 간격 업데이트 실패")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/now")
async def run_crawl_now():
    """즉시 크롤링 실행"""
    try:
        success = crawler_service.run_crawl_now()
        if success:
            return {"message": "크롤링이 즉시 실행되었습니다", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=500, detail="크롤링 실행 실패")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/firebase/stats")
async def get_firebase_stats():
    """Firebase 통계 정보 조회"""
    try:
        stats = await crawler_service.get_firebase_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/firebase/sync")
async def sync_to_firebase():
    """로컬 데이터를 Firebase에 동기화"""
    try:
        result = await crawler_service.sync_to_firebase()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/firebase/test")
async def test_firebase_connection():
    """Firebase 연결 테스트"""
    try:
        result = await crawler_service.test_firebase_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
