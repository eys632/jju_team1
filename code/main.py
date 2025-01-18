import streamlit as st
import os
import tempfile
import logging
from dotenv import load_dotenv
from loaders.secure_file_loader import SecureFileLoader
from services.qna_service import QnAService
from utils.helper_functions import preprocess_text
from functools import lru_cache
from werkzeug.utils import secure_filename
import magic  # 파일 MIME 타입 확인을 위해 필요
import shutil

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# MIME 타입 확인을 위한 매직 인스턴스 생성
mime = magic.Magic(mime=True)

@st.cache_data(show_spinner=False)
def load_pdf_cached(loader, file_path):
    return loader.load_pdf(file_path)

def validate_pdf(file_path):
    """
    업로드된 파일이 실제 PDF인지 확인하는 함수
    """
    try:
        mime_type = mime.from_file(file_path)
        if mime_type != 'application/pdf':
            return False
        # 추가적인 PDF 파일 서명(header) 확인 가능
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False
        return True
    except Exception as e:
        logging.error(f"파일 검증 중 오류 발생: {e}")
        return False

def main():
    st.set_page_config(page_title="📄 논문 GPT", layout="wide")
    st.title("📄 논문 GPT")

    # Session State 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "qna_service" not in st.session_state:
        st.session_state.qna_service = None
    if "pdf_text" not in st.session_state:
        st.session_state.pdf_text = ""

    # Sidebar - 파일 업로드
    st.sidebar.title("📂 논문 업로드")
    uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

    if uploaded_file is not None:
        filename = secure_filename(uploaded_file.name)
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                file_path = os.path.join(tmpdirname, filename)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                logging.info(f"파일 업로드 성공: {filename}")

                # 파일 유효성 검사
                if not validate_pdf(file_path):
                    st.sidebar.error("⚠️ 유효한 PDF 파일이 아닙니다.")
                    logging.warning(f"유효하지 않은 PDF 파일 업로드: {filename}")
                else:
                    st.sidebar.success("✅ 파일 업로드 및 검증 완료!")

                    # PDF 텍스트 로딩 (캐싱 사용)
                    try:
                        with st.sidebar.spinner("📄 PDF 로딩 중..."):
                            loader = SecureFileLoader()
                            pdf_text = load_pdf_cached(loader, file_path)
                        st.session_state.pdf_text = pdf_text
                        st.sidebar.text_area(
                            "📄 논문 내용 미리보기",
                            pdf_text[:1000],  # 미리보기 텍스트 길이 조정
                            height=300,
                            disabled=True
                        )
                        logging.info(f"PDF 텍스트 로딩 성공: {filename}")
                    except Exception as e:
                        st.sidebar.error("⚠️ PDF 로딩 중 오류가 발생했습니다.")
                        logging.error(f"PDF 로딩 오류 ({filename}): {e}")
        except Exception as e:
            st.sidebar.error("⚠️ 파일 업로드 중 오류가 발생했습니다.")
            logging.error(f"파일 업로드 오류: {e}")

    # 채팅 메시지 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["type"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(message["content"])

    # 질문 처리 함수
    def handle_question(question):
        if not question.strip():
            st.warning("⚠️ 질문을 입력해 주세요.")
            return

        if not st.session_state.pdf_text:
            st.warning("⚠️ 먼저 논문을 업로드해 주세요.")
            return

        if st.session_state.qna_service is None:
            try:
                st.session_state.qna_service = QnAService(st.session_state.pdf_text)
                logging.info("QnA 서비스 초기화 성공")
            except Exception as e:
                st.error("⚠️ QnA 서비스 초기화 중 오류가 발생했습니다.")
                logging.error(f"QnA 서비스 초기화 오류: {e}")
                return

        qna_service = st.session_state.qna_service

        try:
            # 사용자 질문 추가
            st.session_state.messages.append({"type": "user", "content": question})
            # 답변 생성 중 표시
            with st.spinner("🕒 답변을 생성 중입니다..."):
                answer = qna_service.get_answer(preprocess_text(question))
            # 답변 추가
            st.session_state.messages.append({"type": "assistant", "content": answer})
            logging.info(f"질문 처리 성공: {question}")
        except Exception as e:
            st.error("⚠️ 답변 생성 중 오류가 발생했습니다.")
            logging.error(f"답변 생성 오류: {e}")

    # 하단 고정 입력 창
    user_input = st.chat_input("질문을 입력하세요...")
    if user_input:
        handle_question(user_input)

    # 파일 업로드 후 임시 디렉토리 정리
    # tempfile.TemporaryDirectory()는 with 블록을 벗어나면 자동으로 삭제되므로 별도 처리 필요 없음

if __name__ == "__main__":
    main()
