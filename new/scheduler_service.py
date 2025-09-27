import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import Callable, Optional
import threading
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

class SchedulerService:
    def __init__(self):
        """스케줄러 서비스 초기화"""
        self.is_running = False
        self.scheduler_thread = None
        self.crawl_interval = int(os.getenv('CRAWL_INTERVAL_MINUTES', 5))
        self.crawl_callback: Optional[Callable] = None
        
        logging.info(f"스케줄러 서비스 초기화 완료 - 크롤링 간격: {self.crawl_interval}분")
    
    def set_crawl_callback(self, callback: Callable):
        """크롤링 콜백 함수 설정"""
        self.crawl_callback = callback
        logging.info("크롤링 콜백 함수 설정 완료")
    
    def _run_scheduler(self):
        """스케줄러 실행 (별도 스레드에서)"""
        logging.info("스케줄러 스레드 시작")
        
        # 즉시 한 번 실행
        if self.crawl_callback:
            try:
                logging.info("초기 크롤링 실행")
                asyncio.run(self.crawl_callback())
            except Exception as e:
                logging.error(f"초기 크롤링 실행 실패: {e}")
        
        # 주기적 실행 설정
        schedule.every(self.crawl_interval).minutes.do(self._execute_crawl)
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 30초마다 스케줄 체크
            except Exception as e:
                logging.error(f"스케줄러 실행 중 오류: {e}")
                time.sleep(60)  # 오류 발생 시 1분 대기
        
        logging.info("스케줄러 스레드 종료")
    
    def _execute_crawl(self):
        """크롤링 실행"""
        if not self.crawl_callback:
            logging.warning("크롤링 콜백 함수가 설정되지 않았습니다.")
            return
        
        try:
            logging.info(f"스케줄된 크롤링 실행 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            asyncio.run(self.crawl_callback())
            logging.info("스케줄된 크롤링 실행 완료")
        except Exception as e:
            logging.error(f"스케줄된 크롤링 실행 실패: {e}")
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logging.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        if not self.crawl_callback:
            logging.error("크롤링 콜백 함수가 설정되지 않았습니다.")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logging.info(f"스케줄러 시작 - {self.crawl_interval}분마다 크롤링 실행")
    
    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            logging.warning("스케줄러가 실행 중이 아닙니다.")
            return
        
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=3)  # 5초 → 3초로 단축
        
        schedule.clear()
        logging.info("스케줄러 중지 완료")
    
    def stop_scheduler(self):
        """스케줄러 중지 (별칭)"""
        self.stop()
    
    def force_stop(self):
        """강제 중지 (즉시 종료)"""
        logging.info("스케줄러 강제 중지...")
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            # 스레드 강제 종료는 위험하므로 플래그만 설정
            logging.info("스케줄러 스레드 종료 신호 전송 완료")
    
    def get_status(self) -> dict:
        """스케줄러 상태 조회"""
        next_run = None
        if schedule.jobs:
            next_run = schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'is_running': self.is_running,
            'crawl_interval_minutes': self.crawl_interval,
            'next_run': next_run,
            'callback_set': self.crawl_callback is not None,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def update_interval(self, minutes: int):
        """크롤링 간격 업데이트"""
        if minutes < 1:
            logging.error("크롤링 간격은 최소 1분 이상이어야 합니다.")
            return False
        
        old_interval = self.crawl_interval
        self.crawl_interval = minutes
        
        # 실행 중이면 스케줄 다시 설정
        if self.is_running:
            schedule.clear()
            schedule.every(self.crawl_interval).minutes.do(self._execute_crawl)
            logging.info(f"크롤링 간격 업데이트: {old_interval}분 → {minutes}분")
        
        return True
    
    def run_now(self):
        """즉시 크롤링 실행"""
        if not self.crawl_callback:
            logging.error("크롤링 콜백 함수가 설정되지 않았습니다.")
            return False
        
        try:
            logging.info("수동 크롤링 실행")
            
            # 별도 스레드에서 비동기 크롤링 실행
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_async_crawl():
                try:
                    # 새 이벤트 루프에서 실행
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.crawl_callback())
                    loop.close()
                    result_queue.put(("success", None))
                except Exception as e:
                    result_queue.put(("error", e))
            
            # 별도 스레드에서 실행
            thread = threading.Thread(target=run_async_crawl)
            thread.start()
            thread.join(timeout=300)  # 5분 타임아웃
            
            if thread.is_alive():
                logging.error("크롤링 타임아웃 (5분 초과)")
                return False
            
            # 결과 확인
            if not result_queue.empty():
                result_type, error = result_queue.get()
                if result_type == "success":
                    logging.info("수동 크롤링 완료")
                    return True
                else:
                    logging.error(f"수동 크롤링 실행 실패: {error}")
                    return False
            else:
                logging.error("크롤링 결과를 받지 못했습니다")
                return False
                
        except Exception as e:
            logging.error(f"수동 크롤링 실행 실패: {e}")
            return False

