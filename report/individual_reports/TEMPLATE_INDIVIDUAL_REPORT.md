    # Individual Report: Lab 3 - Chatbot vs ReAct Agent

    - **Student Name**: [Lê Quang Minh]
    - **Student ID**: [2A202600801]
    - **Date**: [01/06/2026]

    ---

 I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase.*

Trong dự án này, em đảm nhận vai trò thiết kế **Kiến trúc Lõi (Core Architecture)** của hệ thống Agent, bao gồm vòng lặp tư duy ReAct và các công cụ thực thi (Tools).

- **Modules Implementated**: `src/agent/agent.py` (ReAct Loop V2), `src/agent/agent_v1.py` (Baseline Agent), `src/tools/travel_tools.py`.
- **Code Highlights**: 
  Thành tựu lớn nhất là thuật toán Parse JSON chống đứt gãy và vòng lặp Tự sửa lỗi (Self-Correction):
  ```python
  # Bullet-proof JSON parser
  start_idx = raw_action_text.find("{")
  end_idx = raw_action_text.rfind("}")
  # Feed error back to memory if LLM generates bad JSON
  except Exception as e:
      agent_memory += f"Observation: Lỗi Parse JSON Action: {str(e)}.\n"
Documentation: Em xây dựng class AgenticAgent điều phối chu trình Thought -> Action -> Observation. Khắc phục điểm yếu chí mạng của LLM là hay sinh sai định dạng JSON bằng cách ép nó tự đọc lỗi (Exception) và sinh lại chuỗi mới. Cung cấp các Tools thao tác với file CSV.

II. Debugging Case Study (10 Points)
Analyze a specific failure event you encountered during the lab using the logging system.

Problem Description: Ở bản Agent V1, hệ thống liên tục bị văng lỗi và kẹt vòng lặp do không thể đọc được lệnh Action của LLM.

Log Source: {"event": "PARSING_ERROR", "data": {"error": "Lỗi Parse JSON: Expecting ',' delimiter: line 1 column 77 (char 76)"}}

Diagnosis: LLM sinh ra Action chứa JSON lồng nhau (Nested JSON). Tuy nhiên, đoạn mã Regex cũ re.search(r"Action:\s*(\{.*?\})") dùng .*? (Lazy match) đã cắt sai chuỗi ở dấu ngoặc đóng } đầu tiên, làm hỏng cấu trúc JSON.

Solution: Em đã nâng cấp lên bản V2. Loại bỏ Regex, thay bằng thuật toán tìm biên .find("{") và .rfind("}") để bắt trọn khối JSON lớn nhất. Bổ sung MAX_RETRIES để Agent tự sửa lỗi.

III. Personal Insights: Chatbot vs ReAct (10 Points)
Reflect on the reasoning capability difference.

Reasoning: Khối Thought ép LLM phải "Lập kế hoạch" trước khi nói. Thay vì bịa số liệu doanh thu Phú Quốc như Chatbot, Agent nhận thức được nó thiếu dữ liệu và quyết định gọi Tool đọc CSV.

Reliability: ReAct Agent kém ổn định hơn Chatbot ở các bước trung gian. Nếu Tool bị lỗi hoặc Parse JSON hỏng, Agent sẽ thất bại toàn tập, trong khi Chatbot luôn có thể sinh ra một câu trả lời (dù sai sự thật).

Observation: Observation đóng vai trò "nắn chỉnh" LLM với thực tế. Khi truyền một mã ID sai vào Tool, Tool trả về "Không tìm thấy". Agent lập tức đổi hướng suy nghĩ và xin lỗi người dùng.

IV. Future Improvements (5 Points)
How would you scale this for a production-level AI agent system?

Scalability: Áp dụng RAG (Retrieval-Augmented Generation) kết hợp Vector DB để thay vì nạp toàn bộ file CSV vào bộ nhớ, Agent chỉ trích xuất đúng 3 dòng dữ liệu liên quan nhất.

Safety: Yêu cầu xác nhận từ con người (Human-in-the-loop) trước khi thực thi các Tool nhạy cảm.

Performance: Chuyển kiến trúc vòng lặp while sang LangGraph để quản lý State chuyên nghiệp, cho phép rẽ nhánh phức tạp.
    > Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
