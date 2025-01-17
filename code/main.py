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

    col1, col2 = st.columns([1, 2])

    with col1:
        # 파일 업로드
        uploaded_file = st.file_uploader("📂 논문 PDF 업로드", type=["pdf"])
        if uploaded_file is not None:
            loader = SecureFileLoader()
            file_path = os.path.join(loader.base_dir, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("✅ 파일 업로드 완료!")
            except Exception as e:
                st.error(f"⚠️ 파일 업로드 중 오류 발생: {e}")
                return

            # PDF 텍스트 로드
            try:
                pdf_text = loader.load_pdf(uploaded_file.name)
                st.text_area("📝 논문 내용", pdf_text, height=300)
            except Exception as e:
                st.error(f"⚠️ PDF 로딩 오류: {e}")
                return

    with col2:
        # 질문 입력
        question = st.text_input("❓ 질문을 입력하세요")
        if st.button("🔍 답변"):
            if not question.strip():
                st.warning("⚠️ 질문을 입력해 주세요.")
                return
            qna_service = QnAService(pdf_text)
            processed_question = preprocess_text(question)
            answer = qna_service.get_answer(processed_question)
            st.write("📝 **답변:**", answer)

if __name__ == "__main__":
    main()
