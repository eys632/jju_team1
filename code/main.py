# main.py
import streamlit as st
import os
import logging
from dotenv import load_dotenv
from preprocess import load_index
from services.qna_service import QnAService
from utils.helper_functions import preprocess_text
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def secure_filename_custom(filename):
    """
    파일명에서 안전하지 않은 문자를 제거하는 함수
    """
    return re.sub(r'[^A-Za-z0-9_.-]', '_', filename)

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
    if "index_built" not in st.session_state:
        st.session_state.index_built = False

    # Sidebar - 파일 업로드
    st.sidebar.title("📂 논문 업로드")
    uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

    if uploaded_file is not None:
        filename = secure_filename_custom(uploaded_file.name)
        base_dir = "uploaded_pdfs"

        # base_dir가 존재하지 않으면 생성
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir)
                logging.info(f"base_dir 생성: {base_dir}")
            except Exception as e:
                st.sidebar.error("⚠️ 파일을 저장할 디렉토리를 생성할 수 없습니다.")
                logging.error(f"base_dir 생성 오류: {e}")
                return

        file_path = os.path.join(base_dir, filename)
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logging.info(f"파일 업로드 성공: {filename}")
        except Exception as e:
            st.sidebar.error("⚠️ 파일 업로드 중 오류가 발생했습니다.")
            logging.error(f"파일 업로드 오류: {e}")
            return

        # 파일 유효성 검사
        if not validate_pdf(file_path):
            st.sidebar.error("⚠️ 유효한 PDF 파일이 아닙니다.")
            logging.warning(f"유효하지 않은 PDF 파일 업로드: {filename}")
        else:
            st.sidebar.success("✅ 파일 업로드 및 검증 완료!")
            st.session_state.pdf_text = filename  # 파일명 저장

            # PDF 텍스트 로딩 및 인덱스 구축
            try:
                if not st.session_state.index_built:
                    st.sidebar.info("📄 PDF 로딩 및 인덱스 생성 중...")
                    paragraphs, index = load_index(file_path)
                    st.session_state.index = index
                    st.session_state.paragraphs = paragraphs
                    st.session_state.index_built = True
                    st.sidebar.success("✅ PDF 로딩 및 인덱스 생성 완료!")
                    logging.info(f"PDF 텍스트 로딩 및 인덱스 생성 성공: {filename}")
            except Exception as e:
                st.sidebar.error("⚠️ PDF 로딩 중 오류가 발생했습니다.")
                logging.error(f"PDF 로딩 오류 ({filename}): {e}")

    # 질문 처리 함수
    def handle_question(question):
        if not question.strip():
            st.warning("⚠️ 질문을 입력해 주세요.")
            return

        if not st.session_state.pdf_text:
            st.warning("⚠️ 먼저 논문을 업로드해 주세요.")
            return

        if not st.session_state.index_built:
            st.warning("⚠️ 논문 인덱스가 아직 생성되지 않았습니다. 잠시만 기다려 주세요.")
            return

        try:
            # 질문 임베딩 생성
            model = SentenceTransformer('all-MiniLM-L6-v2')
            question_embedding = model.encode([question])

            # FAISS 인덱스 로드
            index = st.session_state.index
            paragraphs = st.session_state.paragraphs

            # 유사한 상위 5개 단락 검색
            D, I = index.search(question_embedding, 5)
            relevant_paragraphs = [paragraphs[i] for i in I[0]]

            # 관련 단락 결합
            context = "\n".join(relevant_paragraphs)

            # QnA 서비스 초기화
            qna_service = QnAService(context)
            answer = qna_service.get_answer(preprocess_text(question))

            # 사용자 질문 및 답변 추가
            st.session_state.messages.append({"type": "user", "content": question})
            st.session_state.messages.append({"type": "assistant", "content": answer})
            logging.info(f"질문 처리 성공: {question}")

        except Exception as e:
            st.error("⚠️ 답변 생성 중 오류가 발생했습니다.")
            logging.error(f"답변 생성 오류: {e}")

    # Handle user input
    user_input = st.chat_input("질문을 입력하세요...")
    if user_input:
        with st.spinner("🕒 답변을 생성 중입니다..."):
            handle_question(user_input)

    # 채팅 메시지 표시
    with st.container():
        for message in st.session_state.messages:
            if message["type"] == "user":
                st.markdown(f"**👤 질문:** {message['content']}")
            else:
                st.markdown(f"**🤖 답변:** {message['content']}")

def validate_pdf(file_path):
    """
    업로드된 파일이 실제 PDF인지 확인하는 함수
    """
    try:
        mime_type = magic.from_file(file_path, mime=True)
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

if __name__ == "__main__":
    main()
