# services/qna_service.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging
from .search_service import SearchService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QnAService:
    def __init__(self, data: str):
        self.data = data
        self.chat_model = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.0
        )
        self.search_service = SearchService(data)

    def get_answer(self, question: str) -> str:
        """
        질문에 대한 답변을 생성합니다.
        :param question: 사용자의 질문
        :return: 생성된 답변
        """
        system_prompt = "You are a helpful assistant."
        user_prompt = question

        # 관련 문서 검색
        relevant_docs = self.search_service.search(user_prompt)
        context = "\n".join(relevant_docs)

        # ChatGPT에 전달할 메시지 구성
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {user_prompt}")
        ]

        try:
            response = self.chat_model.invoke(messages)
            answer = response.content.strip()
            logger.info(f"Generated answer for question: {question}")
            return answer
        except Exception as e:
            logger.error(f"Error generating answer for question '{question}': {e}")
            return "Error generating response."
