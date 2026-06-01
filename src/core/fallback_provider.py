from src.core.llm_provider import LLMProvider

class FallbackProvider(LLMProvider):
    def __init__(self, providers: list[LLMProvider]):
        self.providers = providers

    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        errors = []
        # Duyệt qua từng Provider theo thứ tự ưu tiên
        for provider in self.providers:
            try:
                # Cố gắng sinh câu trả lời
                return provider.generate(system_prompt, user_prompt)
            except Exception as e:
                # Nếu lỗi, ghi nhận lại và chạy tiếp vòng lặp sang Provider tiếp theo
                print(f"[Fallback] {provider.__class__.__name__} thất bại ({str(e)}). Đang chuyển luồng...")
                errors.append(str(e))
        
        # Nếu tất cả các luồng (Gemini và OpenAI) đều chết
        return {
            "text": f'Thought: Tất cả các hệ thống AI đều đang quá tải.\nAction: {{"tool": "Final Answer", "args": {{"answer": "Hệ thống AI đang gặp sự cố diện rộng. Vui lòng thử lại sau. Chi tiết lỗi: {errors}"}}}}',
            "prompt_tokens": 0,
            "completion_tokens": 0
        }