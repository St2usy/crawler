#!/usr/bin/env python3
"""
개선된 서버 실행 스크립트 - 빠른 종료 지원
"""
import subprocess
import os
import sys
import signal
import time
import psutil

def find_server_process():
    """실행 중인 서버 프로세스 찾기"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'uvicorn' in cmdline and 'app:app' in cmdline:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def kill_existing_servers():
    """기존 서버 프로세스 종료"""
    print("🔍 기존 서버 프로세스 확인 중...")
    
    server_proc = find_server_process()
    if server_proc:
        print(f"🛑 기존 서버 프로세스 발견 (PID: {server_proc.pid})")
        try:
            # Graceful shutdown 시도
            server_proc.terminate()
            server_proc.wait(timeout=5)
            print("✅ 기존 서버가 정상적으로 종료되었습니다")
        except psutil.TimeoutExpired:
            print("⚠️ 정상 종료 실패, 강제 종료 중...")
            server_proc.kill()
            server_proc.wait(timeout=2)
            print("✅ 기존 서버가 강제 종료되었습니다")
        except Exception as e:
            print(f"❌ 서버 종료 중 오류: {e}")
    else:
        print("✅ 실행 중인 서버가 없습니다")

def start_server():
    """서버 시작"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print("🚀 개선된 FastAPI 크롤러 서버 시작 중...")
    print(f"📁 작업 디렉토리: {current_dir}")
    print("🌐 서버 주소: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("⚡ 빠른 종료: Ctrl+C")
    print("=" * 50)
    
    try:
        # uvicorn으로 서버 시작
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info",
            "--timeout-keep-alive", "5",  # Keep-alive 타임아웃 단축
            "--limit-concurrency", "100",  # 동시 연결 수 제한
        ], cwd=current_dir)
        
    except KeyboardInterrupt:
        print("\n👋 서버가 사용자에 의해 중지되었습니다.")
        print("🔄 리소스 정리 중...")
        time.sleep(1)  # 정리 시간 확보
        print("✅ 서버 종료 완료")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류 발생: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    print("=" * 50)
    print("🔥 개선된 FastAPI 크롤러 서버")
    print("=" * 50)
    
    # 기존 서버 프로세스 종료
    kill_existing_servers()
    
    # 서버 시작
    start_server()

if __name__ == "__main__":
    main()

