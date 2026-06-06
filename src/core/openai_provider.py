import os
from openai import OpenAI
from src.core.llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name="gpt-4o-mini"):  # Dùng gpt-4o-mini cho rẻ và cực nhanh
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy OPENAI_API_KEY.")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        
        return {
            "text": response.choices[0].message.content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }