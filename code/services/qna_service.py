# services/qna_service.py

import openai
import os
from dotenv import load_dotenv

load_dotenv()

class QnAService:
    def __init__(self, context):
        self.context = context
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    def get_answer(self, question):
        prompt = f"다음 논문 내용을 바탕으로 질문에 답변해주세요.\n\n논문 내용:\n{self.context}\n\n질문: {question}\n답변:"
        
        response = openai.Completion.create(
            engine="text-davinci-003",  # 원하는 엔진으로 변경 가능
            prompt=prompt,
            max_tokens=500,
            temperature=0.3,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        answer = response.choices[0].text.strip()
        return answer
