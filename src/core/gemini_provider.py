import os
from google import genai
from google.genai import types
from src.core.llm_provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name="gemini-2.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong biến môi trường.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,  # Giảm sáng tạo để tăng tính chính xác khi chạy ReAct
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=config
        )
        
        # Trích xuất số token tiêu thụ
        prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
        
        return {
            "text": response.text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }