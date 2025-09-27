#!/usr/bin/env python3
"""
FastAPI 크롤러 서버 실행 스크립트
"""
import subprocess
import os
import sys

if __name__ == "__main__":
    # 현재 디렉토리를 Python 경로에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print("🚀 FastAPI 크롤러 서버 시작 중...")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🔍 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("\n" + "="*50)
    
    try:
        # python -m uvicorn을 사용하여 서버 실행
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ], cwd=current_dir)
    except KeyboardInterrupt:
        print("\n👋 서버가 사용자에 의해 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류 발생: {e}")
        sys.exit(1)
