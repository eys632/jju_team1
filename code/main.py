import streamlit as st
import os
from dotenv import load_dotenv
from loaders.secure_file_loader import SecureFileLoader
from services.qna_service import QnAService
from utils.helper_functions import preprocess_text

# 환경 변수 로드
load_dotenv()

def main():
    st.set_page_config(page_title="논문 Q&A 시스템", layout="wide")
    st.title("📄 논문 Q&A 시스템")

    # Custom CSS 추가: 입력창 하단 고정
    st.markdown("""
        <style>
        /* 전체 페이지 레이아웃 */
        .main-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        /* 스크롤 가능한 콘텐츠 */
        .scrollable-content {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 80px; /* 하단 입력창 공간 */
        }
        /* 고정된 하단 바 */
        .fixed-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f8f9fa;
            padding: 10px;
            border-top: 1px solid #ddd;
            z-index: 1000;
        }
        </style>
    """, unsafe_allow_html=True)

    # Session State 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

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
    st.markdown('<div class="scrollable-content">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        if message["type"] == "user":
            st.markdown(f"""
            <div style="text-align: right; margin: 10px 0;">
                <div style="display: inline-block; padding: 10px; border-radius: 10px; background-color: #dcf8c6;">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: left; margin: 10px 0;">
                <div style="display: inline-block; padding: 10px; border-radius: 10px; background-color: #f1f0f0;">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 질문 처리 함수
    def handle_question():
        question = st.session_state.user_input
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
            st.session_state.messages.append({"type": "bot", "content": answer})
        except Exception as e:
            st.error(f"⚠️ 답변 생성 중 오류: {e}")

        st.session_state.user_input = ""

    # 고정된 하단 바 추가
    st.markdown("""
        <div class="fixed-footer">
            <form action="#">
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="user_input" name="user_input" placeholder="질문을 입력하세요" style="flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 1rem;">
                    <button type="submit" style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">📤 질문하기</button>
                </div>
            </form>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
