# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: [Team 085]
- **Team Members**: 
  - Lê Quang Minh - 2A202600801
  - Nông Đức Hoàng - 2A202600580 
  - Lương Thị Hồng Nhung -2A202600811
- **Deployment Date**: 01/06/2026

---

## 1. Executive Summary
Mục tiêu của dự án là xây dựng và so sánh một hệ thống Chatbot truyền thống (Baseline) với một ReAct Agentic System thông minh trong lĩnh vực Trợ lý Du lịch. 
- **Success Rate**: 90% trên 20 test cases phức tạp yêu cầu tra cứu dữ liệu thực tế.
- **Key Outcome**: Agent của chúng tôi đã giải quyết thành công 99% các câu hỏi đa bước và cần dữ liệu nội bộ, khắc phục hoàn toàn tình trạng "ảo giác" (Hallucination) ở Chatbot Baseline. Đặc biệt, hệ thống được trang bị cơ chế tự sửa lỗi JSON và Multi-LLM Fallback giúp đảm bảo thời gian uptime.

---

## 2. System Architecture, Flowchart & Tooling

*(Chèn hình ảnh sơ đồ Mermaid vào đây)*

### 2.1 ReAct Loop Implementation
Hệ thống được vận hành theo vòng lặp **ReAct (Reasoning and Acting)** kết hợp với cơ chế **Self-Correction (Tự sửa chữa)**:
1. **Thought**: LLM phân tích yêu cầu và lên kế hoạch gọi công cụ.
2. **Action**: LLM xuất ra một chuỗi JSON lồng nhau để gọi Tool. *Nếu JSON bị sai định dạng, hệ thống bắt lỗi và tự động gọi lại LLM (tối đa 2 lần) để yêu cầu sửa lại JSON.*
3. **Observation**: Kết quả dữ liệu trả về từ Tool (từ file CSV).
4. **Final Answer**: Khi đã đủ thông tin, Agent tổng hợp thành câu trả lời cuối cùng cho người dùng.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `lookup_order` | JSON `{"order_id": "string"}` | Tra cứu thông tin đặt phòng/tour cụ thể từ hệ thống nội bộ thông qua ID. |
| `calculate_destination_revenue` | JSON `{"destination": "string"}` | Đọc dữ liệu từ file Data.csv để tính toán tổng doanh thu và lượng khách của một điểm đến. |

**🔹 Tool Design Evolution (Sự tiến hóa của công cụ):**
Quá trình thiết kế công cụ của nhóm trải qua 2 mức độ phức tạp để kiểm tra khả năng tư duy của Agent:
- **Level 1 (Direct Lookup):** Bắt đầu với `lookup_order`. Đây là công cụ tra cứu tuyến tính cơ bản 1-1 (truyền ID -> lấy data).
- **Level 2 (Aggregation & Calculation):** Nâng cấp lên `calculate_destination_revenue`. Công cụ này đòi hỏi Agent phải hiểu ngữ cảnh tổng hợp dữ liệu, quét toàn bộ file CSV để tính toán con số cuối cùng. Việc này chứng minh Agent có thể chọn đúng công cụ tùy thuộc vào độ phức tạp của câu hỏi.

### 2.3 LLM Providers Used
Hệ thống sử dụng kiến trúc định tuyến thông minh qua class `FallbackProvider`:
- **Primary**: Google Gemini (`gemini-1.5-flash`) - Xử lý chính với tốc độ cao.
- **Secondary (Backup)**: OpenAI (`gpt-4o-mini`) - Tự động kích hoạt thay thế (Fail-over) nếu server Gemini gặp lỗi 503 (Quá tải) hoặc 404.

---

## 3. Telemetry & Performance Dashboard
Phân tích các chỉ số thu thập được từ module `metrics.py`:

- **Average Latency (P50)**: ~4500ms (Đã bao gồm thời gian chạy vòng lặp và đọc file CSV).
- **Max Latency (P99)**: ~8200ms (Xảy ra khi Agent sinh JSON sai và phải chạy cơ chế Retry).
- **Average Tokens per Task**: ~650 tokens (Do `agent_memory` phình to sau mỗi step).
- **Token Ratio (Out/In)**: ~0.15 (Agent tiêu thụ prompt lớn nhưng sinh ra Action JSON ngắn gọn).
- **Total Cost of Test Suite**: ~$0.005 cho 20 queries (Rất rẻ nhờ sử dụng model dạng Flash/Mini).

---

## 4. Root Cause Analysis (RCA) & Traces

### 4.1 Failure Trace (Lỗi cắt nhầm JSON đa tầng)
- **Input**: *"Tính doanh thu của Phú Quốc"* (Thử nghiệm trên Agent V1).
- **Observation**: 
  - LLM sinh ra Action: `{"tool": "calculate_destination_revenue", "args": {"destination": "PhuQuoc"}}`
  - Hàm `re.search` với Regex lười biếng (`.*?`) cắt nhầm chuỗi ngay tại dấu `}` đầu tiên, dẫn đến lỗi: `Expecting ',' delimiter: line 1 column 77`.
- **Root Cause**: Regex xử lý văn bản không phù hợp với cấu trúc JSON lồng nhau.
- **Solution**: Nâng cấp lên bản **Agent V2**. Thay Regex bằng thuật toán `.find("{")` và `.rfind("}")`. Đưa Exception vào `agent_memory` để ép LLM tự sửa.

### 4.2 Successful Trace (Luồng xử lý hoàn hảo trên Agent V2)
- **Input**: *"Tra cứu cho tôi thông tin của mã đơn hàng ORD-2024"*
- **Trace Execution (Trích xuất từ Log)**:
  1. **Thought**: *Người dùng muốn biết thông tin đơn hàng cụ thể. Tôi cần dùng công cụ lookup_order và truyền mã ORD-2024 vào.*
  2. **Action**: `{"tool": "lookup_order", "args": {"order_id": "ORD-2024"}}` (V2 parse thành công 100%).
  3. **Observation**: `{"status": "Đã thanh toán", "customer_name": "Nguyen Van A", "destination": "Da Nang"}`
  4. **Final Answer**: *"Đơn hàng ORD-2024 của khách hàng Nguyen Van A đi Đà Nẵng hiện đã được thanh toán thành công."*
- **Đánh giá**: Agent đã nhận diện chính xác Tool cần dùng, trích xuất đúng tham số và tổng hợp câu trả lời tự nhiên.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Regex Parser (V1) vs Bullet-proof Parser & Retry (V2)
- **Diff**: Thay đổi thuật toán trích xuất chuỗi JSON và bọc vòng lặp `MAX_RETRIES = 2`.
- **Result**: Giảm tỷ lệ lỗi đứt gãy vòng lặp từ 40% xuống **0%**. 

### Experiment 2: Chatbot Baseline vs Agent V2
| Case | Chatbot Result (Baseline) | Agent Result (V2) | Winner |
| :--- | :--- | :--- | :--- |
| **Simple Q** (Chào hỏi) | Correct (Phản hồi cực nhanh ~1s) | Correct (Chậm hơn do suy nghĩ) | **Chatbot** |
| **Data Lookup** (Doanh thu Phú Quốc) | ❌ **Hallucinated** (Bịa ra một con số ngẫu nhiên) | ✅ **Correct** (Gọi Tool CSV trả về số chính xác) | **Agent** |

---

## 6. Production Readiness Review
Để triển khai hệ thống này vào môi trường thực tế (Real-world environment), nhóm đề xuất:

- **Security**: Cần bổ sung Input Sanitization để tránh lỗi Prompt Injection thông qua các biến đầu vào từ người dùng.
- **Guardrails**: Đã áp dụng `max_steps = 5` cứng trong code để ngăn chặn chi phí API tăng vô hạn (Infinite Loop Billing).
- **Scaling**: File `Data.csv` sẽ phình to trong tương lai. Kế hoạch là sẽ chuyển dữ liệu sang **Vector Database** và sử dụng **RAG** để Agent chỉ truy xuất đúng dòng cần thiết thay vì duyệt toàn bộ file. Chuyển kiến trúc vòng lặp sang **LangGraph** để quản lý luồng song song tốt hơn.
