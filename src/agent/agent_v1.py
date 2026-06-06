import json
import re
from src.core.llm_provider import LLMProvider
from src.core.travel_tool import TravelTools
from src.telemetry.logger import logger
from src.telemetry.metrics import metrics_tracker

class AgenticAgentV1:
    def __init__(self, provider: LLMProvider, tools: TravelTools, max_steps: int = 5):
        self.provider = provider
        self.tools = tools
        self.max_steps = max_steps
        
        # System Prompt cơ bản
        self.system_prompt = """Bạn là một ReAct Agent quản lý du lịch. Bạn LUÔN PHẢI suy luận và hành động theo đúng định dạng sau:
Thought: Suy nghĩ của bạn về việc cần làm tiếp theo.
Action: {"tool": "tên_công_cụ", "args": {"tham_số": "giá_trị"}}

Các công cụ có sẵn:
1. lookup_order: Nhận `order_id`.
2. lookup_customer: Nhận `customer_id`.
3. calculate_destination_revenue: Nhận `destination`.
4. get_destination_weather: Nhận `destination`.
5. Final Answer: Trình bày câu trả lời cuối cùng, dùng tham số `answer`.
"""

    def run(self, user_query: str) -> str:
        agent_memory = f"User Query: {user_query}\n"
        logger.log_event("AGENT_V1_START", {"query": user_query})
        
        for step in range(self.max_steps):
            logger.log_event("LOOP_STEP", {"step": step + 1})
            
            # 1. Gọi LLM
            start_time = metrics_tracker.start_timer()
            llm_output = self.provider.generate(self.system_prompt, agent_memory)
            latency = metrics_tracker.stop_timer(start_time)
            
            response_text = llm_output["text"]
            metrics_tracker.record_metrics(
                llm_output["prompt_tokens"], 
                llm_output["completion_tokens"], 
                latency, 
                self.provider.__class__.__name__
            )
            logger.log_event("LLM_RESPONSE", {"raw_text": response_text})
            
            agent_memory += f"{response_text}\n"

            # =================================================================
            # 2. PARSE ACTION (PHIÊN BẢN V1 - DỄ BỊ LỖI, KHÔNG CÓ RETRY)
            # =================================================================
            # Sử dụng Regex lười biếng (.*?), rất dễ cắt nhầm nếu JSON có lồng nhau
            action_match = re.search(r"Action:\s*(\{.*?\})", response_text, re.DOTALL)
            
            if not action_match:
                obs = "Lỗi định dạng: Không tìm thấy JSON."
                agent_memory += f"Observation: {obs}\n"
                logger.log_event("PARSING_ERROR", {"error": obs})
                continue # Bỏ qua, làm lãng phí 1 step trong max_steps
                
            try:
                # Parse thẳng, nếu LLM sinh chuỗi thiếu ngoặc sẽ văng lỗi ngay
                action_data = json.loads(action_match.group(1).strip())
                tool_name = action_data.get("tool")
                tool_args = action_data.get("args", {})
            except Exception as e:
                obs = f"Lỗi Parse JSON: {str(e)}"
                agent_memory += f"Observation: {obs}\n"
                logger.log_event("PARSING_ERROR", {"error": obs})
                continue # Không có vòng lặp tự sửa, Agent sẽ mất 1 step
            
            # 3. THỰC THI TOOL
            if tool_name == "Final Answer":
                return tool_args.get("answer", "Không có câu trả lời.")
                
            try:
                if tool_name == "lookup_order":
                    observation = self.tools.lookup_order(**tool_args)
                elif tool_name == "lookup_customer":
                    observation = self.tools.lookup_customer(**tool_args)
                elif tool_name == "calculate_destination_revenue":
                    observation = self.tools.calculate_destination_revenue(**tool_args)
                elif tool_name == "get_destination_weather":
                    observation = self.tools.get_destination_weather(**tool_args)
                else:
                    observation = f"Lỗi: Công cụ '{tool_name}' không tồn tại."
            except Exception as e:
                observation = f"Lỗi khi chạy công cụ: {str(e)}"
                
            agent_memory += f"Observation: {observation}\n"
            logger.log_event("TOOL_EXECUTION", {"tool": tool_name, "observation": observation})
            
        return "Hệ thống Agent V1 đã hết số bước thực thi (Max steps) mà không tìm được kết quả do gặp quá nhiều lỗi Parsing."