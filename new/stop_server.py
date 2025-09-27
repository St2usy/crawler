#!/usr/bin/env python3
"""
서버 빠른 종료 스크립트
"""
import psutil
import time
import sys

def stop_server():
    """서버 프로세스 종료"""
    print("🔍 서버 프로세스 찾는 중...")
    
    server_found = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'uvicorn' in cmdline and 'app:app' in cmdline:
                    server_found = True
                    print(f"🛑 서버 프로세스 발견 (PID: {proc.pid})")
                    
                    # Graceful shutdown 시도
                    print("🔄 정상 종료 시도 중...")
                    proc.terminate()
                    
                    try:
                        proc.wait(timeout=3)  # 3초 대기
                        print("✅ 서버가 정상적으로 종료되었습니다")
                    except psutil.TimeoutExpired:
                        print("⚠️ 정상 종료 실패, 강제 종료 중...")
                        proc.kill()
                        proc.wait(timeout=1)
                        print("✅ 서버가 강제 종료되었습니다")
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print(f"❌ 프로세스 처리 중 오류: {e}")
    
    if not server_found:
        print("ℹ️ 실행 중인 서버 프로세스를 찾을 수 없습니다")
    
    print("🏁 서버 종료 작업 완료")

if __name__ == "__main__":
    print("=" * 40)
    print("🛑 서버 종료 도구")
    print("=" * 40)
    
    stop_server()
    
    print("=" * 40)

