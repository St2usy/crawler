from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NoticeResponse(BaseModel):
    """공지사항 응답 모델"""
    id: str
    category: str
    number: str
    title: str
    author: str
    date: str
    attachments: str
    views: str
    url: str
    content: str
    content_html: str
    image_urls: List[str]
    crawled_at: str

class CrawlStatus(BaseModel):
    """크롤링 상태 모델"""
    status: str  # "idle", "running", "completed", "error"
    message: str
    timestamp: str
    last_crawl_time: Optional[str] = None
    total_notices: Optional[int] = None

class CategorySummary(BaseModel):
    """카테고리별 요약 모델"""
    category: str
    count: int
    latest_date: Optional[str] = None

class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 20

class CrawlRequest(BaseModel):
    """크롤링 요청 모델"""
    max_pages: Optional[int] = 2
    use_threading: Optional[bool] = True
