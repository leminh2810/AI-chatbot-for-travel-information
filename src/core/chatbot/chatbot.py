from src.core.llm_provider import LLMProvider

class BasicChatbot:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.system_prompt = """Bạn là một trợ lý du lịch ảo. Nhiệm vụ của bạn là trả lời các câu hỏi dựa trên kiến thức có sẵn. Bạn KHÔNG có quyền truy cập vào cơ sở dữ liệu nội bộ."""

    def run(self, user_query: str) -> str:
        # Chatbot truyền thống chỉ nhận query và trả lời thẳng
        llm_output = self.provider.generate(self.system_prompt, user_query)
        return llm_output["text"]