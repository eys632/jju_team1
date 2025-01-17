# main.py

import os
from dotenv import load_dotenv
from QnA import run_qna  # 파일명 변경 후 QnA.py로 임포트

def main():
    # .env 로드 (QnA.py에서도 이미 로드하므로 중복 로드할 필요는 없지만, 필요 시 유지)
    load_dotenv()
    
    print("=== Q&A 프로세스 시작 ===")
    run_qna()
    print("=== Q&A 프로세스 종료 ===")

if __name__ == "__main__":
    main()
