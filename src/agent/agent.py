import json
import re
from src.core.llm_provider import LLMProvider
from src.core.travel_tool import TravelTools
from src.telemetry.logger import logger
from src.telemetry.metrics import metrics_tracker

class AgenticAgent:
    def __init__(self, provider: LLMProvider, tools: TravelTools, max_steps: int = 5):
        self.provider = provider
        self.tools = tools
        self.max_steps = max_steps
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """Bạn là một Trợ lý Quản lý Hệ thống Du lịch thông minh, vận hành theo cơ chế ReAct (Lập luận và Hành động).
Nhiệm vụ của bạn là giải quyết câu hỏi của người dùng bằng cách suy nghĩ từng bước và sử dụng công cụ một cách hợp lý.

Bạn CÓ THỂ sử dụng các công cụ sau:
1. check_booking_status: Nhận vào `booking_id`. Trả về trạng thái chi tiết của mã booking đó.
2. analyze_customer_history: Nhận vào `customer_id`. Trả về báo cáo lịch sử chuyến đi của khách hàng.
3. calculate_destination_revenue: Nhận vào `destination`. Trả về tổng doanh thu và lượng khách của điểm đến.
4. Final Answer: Trình bày câu trả lời cuối cùng cho người dùng sau khi đã có đủ thông tin.

ĐỊNH DẠNG BẮT BUỘC TRONG MỖI LƯỢT PHẢN HỒI:
Bạn phải luôn luôn xuất đầu ra theo cấu trúc phân tách nghiêm ngặt sau, không được thiếu sót:

Thought: Bạn đang nghĩ gì? Bạn cần tìm thông tin gì tiếp theo? Bạn sẽ chọn công cụ nào?
Action: MỘT CHUỖI JSON DUY NHẤT chứa tên công cụ và các đối số, không bao gồm ký tự dấu nháy code block (```).
Ví dụ:
{"tool": "check_booking_status", "args": {"booking_id": "B00001"}}

LƯU Ý: Khi bạn đã tích lũy đủ thông tin từ các bước Observation để trả lời trọn vẹn câu hỏi, hãy gọi công cụ "Final Answer".
Ví dụ:
Thought: Tôi đã có đầy đủ thông tin doanh thu của Huế. Tôi sẽ trả lời người dùng.
Action: {"tool": "Final Answer", "args": {"answer": "Tổng doanh thu tại Huế đạt X VNĐ..."}}
"""

    def run(self, user_query: str) -> str:
        logger.log_event("AGENT_START", {"query": user_query})
        
        # Khởi tạo bộ nhớ hội thoại tạm thời cho vòng lặp ReAct
        agent_memory = f"User Query: {user_query}\n"
        
        for step in range(1, self.max_steps + 1):
            logger.log_event("LOOP_STEP", {"step": step})
            
            # 1. THOUGHT & ACTION GENERATION
            start_time = metrics_tracker.start_timer()
            llm_output = self.provider.generate(self.system_prompt, agent_memory)
            latency = metrics_tracker.stop_timer(start_time)
            
            # Ghi nhận metric hiệu năng của bước
            metrics = metrics_tracker.record_metrics(
                llm_output["prompt_tokens"], 
                llm_output["completion_tokens"], 
                latency, 
                self.provider.__class__.__name__
            )
            logger.log_event("LLM_METRIC", metrics)
            
            response_text = llm_output["text"]
            logger.log_event("LLM_RESPONSE", {"raw_text": response_text})
            
            # Cập nhật nhật ký vòng lặp cho Agent
            agent_memory += f"\n{response_text}\n"
            
        # ========================================================
            # 2. PARSE ACTION KẾT HỢP RETRY LOGIC (TỰ SỬA LỖI JSON)
            # ========================================================
            MAX_RETRIES = 2
            parse_success = False
            
            for attempt in range(MAX_RETRIES):
                action_match = re.search(r"Action:\s*(.*)", response_text, re.DOTALL)
                
                if not action_match:
                    obs = "Lỗi định dạng: Không tìm thấy từ khóa 'Action:'."
                    agent_memory += f"Observation: {obs}\n"
                    logger.log_event("PARSING_ERROR", {"error": obs, "attempt": attempt + 1})
                    # Gọi lại LLM ngay lập tức để ép nó sửa lỗi
                    response_text = self.provider.generate(self.system_prompt, agent_memory)["text"]
                    continue
                    
                raw_action_text = action_match.group(1).strip()
                
                # Tìm đúng dấu { đầu tiên và dấu } cuối cùng để bắt trọn JSON lồng nhau
                start_idx = raw_action_text.find("{")
                end_idx = raw_action_text.rfind("}")
                
                if start_idx == -1 or end_idx == -1:
                    obs = "Lỗi định dạng: Không tìm thấy cặp ngoặc {} bao bọc JSON."
                    agent_memory += f"Observation: {obs}\n"
                    logger.log_event("PARSING_ERROR", {"error": obs, "attempt": attempt + 1})
                    response_text = self.provider.generate(self.system_prompt, agent_memory)["text"]
                    continue
                    
                try:
                    # Trích xuất và parse chính xác
                    clean_json = raw_action_text[start_idx : end_idx + 1]
                    action_data = json.loads(clean_json)
                    tool_name = action_data.get("tool")
                    tool_args = action_data.get("args", {})
                    
                    parse_success = True
                    break # Parse thành công -> Thoát khỏi vòng lặp Retry ngay
                    
                except Exception as e:
                    obs = f"Lỗi Parse JSON Action: {str(e)}. Yêu cầu chỉ xuất chuỗi JSON sạch, không có văn bản thừa."
                    agent_memory += f"Observation: {obs}\n"
                    logger.log_event("PARSING_ERROR", {"error": obs, "attempt": attempt + 1})
                    response_text = self.provider.generate(self.system_prompt, agent_memory)["text"]
            
            # Nếu Agent thử lại quá số lần quy định mà vẫn sai JSON -> Dừng hệ thống an toàn
            if not parse_success:
                logger.log_event("FATAL_ERROR", {"error": "Vượt quá số lần Retry do LLM liên tục xuất sai JSON."})
                return "Xin lỗi, hệ thống không thể xử lý định dạng dữ liệu vào lúc này. Vui lòng thử lại câu hỏi."
            # 3. EXECUTE ACTION (EXECUTION COUPLING)
            elif tool_name == "calculate_destination_revenue":
                observation = self.tools.calculate_destination_revenue(**tool_args)
            elif tool_name == "get_destination_weather":
                observation = self.tools.get_destination_weather(**tool_args)
            if tool_name == "Final Answer":
                final_ans = tool_args.get("answer", "Không có câu trả lời nào được cấu hình.")
                logger.log_event("AGENT_SUCCESS", {"final_answer": final_ans})
                return final_ans
                
            # Thực thi công cụ dựa trên lựa chọn của LLM
            logger.log_event("TOOL_CALL", {"tool": tool_name, "args": tool_args})
            if tool_name == "check_booking_status":
                observation = self.tools.check_booking_status(**tool_args)
            elif tool_name == "analyze_customer_history":
                observation = self.tools.analyze_customer_history(**tool_args)
            elif tool_name == "calculate_destination_revenue":
                observation = self.tools.calculate_destination_revenue(**tool_args)
            else:
                observation = f"Công cụ '{tool_name}' không tồn tại trong hệ thống."
                
            logger.log_event("TOOL_OBSERVATION", {"observation": observation})
            agent_memory += f"Observation: {observation}\n"
            
        # Nếu vượt quá giới hạn vòng lặp (Infinite Loop Guardrail)
        timeout_msg = "Hệ thống dừng lại do vượt quá số bước cấu hình (Max steps reached) mà không có Final Answer."
        logger.log_event("AGENT_TIMEOUT", {"error": timeout_msg})
        return timeout_msg