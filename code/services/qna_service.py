# services/qna_service.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

class QnAService:
    def __init__(self, research_paper_content):
        """
        연구 논문 내용을 초기화하고 GPT 모델을 설정합니다.
        """
        self.chat_model = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.0
        )
        system_prompt = (
            "You are a helpful assistant. Below is the content of a research paper to help you answer the following questions:\n\n"
            + research_paper_content
        )
        self.system_message = SystemMessage(content=system_prompt)

    def get_answer(self, question):
        """
        질문을 받아 GPT 모델을 통해 답변을 생성합니다.
        """
        messages = [
            self.system_message,
            HumanMessage(content=question)
        ]
        response = self.chat_model.invoke(messages)
        return response.content.strip()
