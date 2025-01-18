import streamlit as st
import os
from dotenv import load_dotenv
from loaders.secure_file_loader import SecureFileLoader
from services.qna_service import QnAService
from utils.helper_functions import preprocess_text

# 환경 변수 로드
load_dotenv()

def main():
    st.set_page_config(page_title="논문 GPT", layout="wide")
    st.title("📄 논문 GPT")

    # Session State 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar - 파일 업로드
    st.sidebar.title("📂 논문 업로드")
    uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    
    if uploaded_file is not None:
        loader = SecureFileLoader()
        file_path = os.path.join(loader.base_dir, uploaded_file.name)
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success("✅ 파일 업로드 완료!")
        except Exception as e:
            st.sidebar.error(f"⚠️ 파일 업로드 중 오류 발생: {e}")
            return

        try:
            pdf_text = loader.load_pdf(uploaded_file.name)
            st.session_state.pdf_text = pdf_text
            st.sidebar.text_area("📄 논문 내용 미리보기", pdf_text[:500], height=200, disabled=True)  # 미리보기
        except Exception as e:
            st.sidebar.error(f"⚠️ PDF 로딩 오류: {e}")
            return

    # 스크롤 가능한 콘텐츠
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

        if "pdf_text" not in st.session_state:
            st.warning("⚠️ 먼저 논문을 업로드해 주세요.")
            return

        if "qna_service" not in st.session_state:
            try:
                st.session_state.qna_service = QnAService(st.session_state.pdf_text)
            except Exception as e:
                st.error(f"⚠️ QnA 서비스 초기화 오류: {e}")
                return

        qna_service = st.session_state.qna_service

        try:
            answer = qna_service.get_answer(preprocess_text(question))
            st.session_state.messages.append({"type": "user", "content": question})
            st.session_state.messages.append({"type": "assistant", "content": answer})
        except Exception as e:
            st.error(f"⚠️ 답변 생성 중 오류: {e}")

    # 하단 고정 입력 창
    user_input = st.chat_input("질문을 입력하세요...")
    if user_input:
        st.session_state.messages.append({"type": "user", "content": user_input})  # 사용자 메시지 추가
        handle_question(user_input)  # 질문 처리
        st.experimental_rerun()  # 상태 업데이트 후 즉시 페이지 갱신

if __name__ == "__main__":
    main()
