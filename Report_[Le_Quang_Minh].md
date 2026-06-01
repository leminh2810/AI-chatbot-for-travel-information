# Individual Report: Lab 3 - Chatbot vs ReAct Agent

**Student Name:** Lê Quang Minh
**Student ID:** 2A202600801
**Date:** 01/06/2026

---

# I. Technical Contribution (15 Points)

## Describe your specific contribution to the codebase

Trong dự án này, em đảm nhận vai trò thiết kế **Kiến trúc Lõi (Core Architecture)** của hệ thống Agent, bao gồm vòng lặp tư duy ReAct và các công cụ thực thi (Tools).

### Modules Implemented

* `src/agent/agent.py` (ReAct Loop V2)
* `src/agent/agent_v1.py` (Baseline Agent)
* `src/tools/travel_tools.py`

### Code Highlights

Thành tựu lớn nhất là xây dựng thuật toán **JSON Parsing chống lỗi** kết hợp với cơ chế **Self-Correction Loop**.

```python
# Bullet-proof JSON parser
start_idx = raw_action_text.find("{")
end_idx = raw_action_text.rfind("}")

# Feed error back to memory if LLM generates bad JSON
except Exception as e:
    agent_memory += f"Observation: Lỗi Parse JSON Action: {str(e)}.\n"
```

### Documentation

Em xây dựng class `AgenticAgent` để điều phối chu trình:

**Thought → Action → Observation**

Hệ thống được thiết kế nhằm khắc phục điểm yếu phổ biến của LLM là thường sinh ra JSON không đúng định dạng. Khi gặp lỗi parse, Agent sẽ ghi nhận thông tin lỗi vào bộ nhớ ngữ cảnh (memory) dưới dạng Observation, sau đó yêu cầu mô hình tự sinh lại Action hợp lệ. Ngoài ra, em cũng phát triển các Tools hỗ trợ thao tác và truy xuất dữ liệu từ file CSV.

---

# II. Debugging Case Study (10 Points)

## Analyze a specific failure event you encountered during the lab using the logging system

### Problem Description

Ở phiên bản Agent V1, hệ thống thường xuyên bị dừng hoặc mắc kẹt trong vòng lặp vì không thể đọc được lệnh Action do LLM sinh ra.

### Log Source

```json
{
  "event": "PARSING_ERROR",
  "data": {
    "error": "Lỗi Parse JSON: Expecting ',' delimiter: line 1 column 77 (char 76)"
  }
}
```

### Diagnosis

Nguyên nhân xuất phát từ việc LLM tạo ra Action chứa **Nested JSON**. Tuy nhiên, đoạn mã Regex cũ:

```python
re.search(r"Action:\s*({.*?})")
```

sử dụng cơ chế **lazy matching (`.*?`)**, khiến biểu thức chỉ lấy đến dấu `}` đầu tiên thay vì toàn bộ cấu trúc JSON. Điều này làm JSON bị cắt ngắn và dẫn đến lỗi khi parse.

### Solution

Em đã nâng cấp hệ thống lên phiên bản ReAct V2 với các thay đổi sau:

1. Loại bỏ hoàn toàn Regex parsing.
2. Sử dụng thuật toán xác định biên JSON:

```python
start_idx = raw_action_text.find("{")
end_idx = raw_action_text.rfind("}")
json_text = raw_action_text[start_idx:end_idx + 1]
```

3. Bổ sung cơ chế `MAX_RETRIES` để Agent có thể tự sửa lỗi nhiều lần trước khi dừng thực thi.
4. Truyền thông tin lỗi vào Observation để LLM tự điều chỉnh đầu ra ở vòng lặp tiếp theo.

Nhờ đó, tỷ lệ lỗi parse giảm đáng kể và Agent có khả năng phục hồi tốt hơn trước các đầu ra không hợp lệ.

---

# III. Personal Insights: Chatbot vs ReAct (10 Points)

## Reflect on the reasoning capability difference

### Reasoning

Khối **Thought** buộc LLM phải lập kế hoạch trước khi trả lời. Thay vì suy đoán hoặc tự tạo ra số liệu doanh thu của Phú Quốc như một Chatbot thông thường, ReAct Agent nhận thức được rằng nó thiếu dữ liệu cần thiết và chủ động gọi Tool để truy xuất dữ liệu từ file CSV.

### Reliability

ReAct Agent mạnh hơn về khả năng suy luận và sử dụng công cụ, nhưng lại kém ổn định hơn Chatbot ở các bước trung gian. Nếu Tool gặp lỗi hoặc quá trình parse Action thất bại, toàn bộ chu trình có thể bị gián đoạn. Trong khi đó, Chatbot truyền thống hầu như luôn đưa ra phản hồi, mặc dù phản hồi đó có thể không chính xác.

### Observation

Observation đóng vai trò là cầu nối giữa mô hình và thực tế. Khi Agent truyền một mã ID không tồn tại vào Tool, Tool sẽ trả về thông báo như:

> "Không tìm thấy dữ liệu."

Agent sau đó sử dụng Observation này để điều chỉnh kế hoạch, thay đổi hướng suy luận hoặc đưa ra lời xin lỗi phù hợp với người dùng. Điều này giúp hệ thống thích nghi tốt hơn với các tình huống thực tế.

---

# IV. Future Improvements (5 Points)

## How would you scale this for a production-level AI agent system?

### Scalability

Tích hợp mô hình **Retrieval-Augmented Generation (RAG)** cùng với **Vector Database**. Thay vì tải toàn bộ dữ liệu CSV vào bộ nhớ, hệ thống chỉ truy xuất những bản ghi liên quan nhất đến truy vấn hiện tại, giúp giảm chi phí xử lý và tăng khả năng mở rộng.

### Safety

Áp dụng cơ chế **Human-in-the-Loop** đối với các hành động có mức độ rủi ro cao. Trước khi Agent thực thi các Tool quan trọng, hệ thống sẽ yêu cầu xác nhận từ người dùng hoặc người giám sát.

### Performance

Chuyển từ kiến trúc vòng lặp `while` sang nền tảng **LangGraph** để quản lý trạng thái Agent một cách chuyên nghiệp hơn. Cách tiếp cận này hỗ trợ các luồng xử lý phức tạp, khả năng rẽ nhánh, song song hóa và theo dõi trạng thái trong môi trường sản xuất.

---

# Conclusion

Qua bài Lab 3, em đã có cơ hội xây dựng và tối ưu một ReAct Agent hoàn chỉnh, từ cơ chế suy luận, sử dụng công cụ đến xử lý lỗi tự động. Kết quả thực nghiệm cho thấy ReAct Agent mang lại khả năng lập kế hoạch và truy xuất thông tin tốt hơn Chatbot truyền thống, mặc dù đòi hỏi kiến trúc phức tạp hơn và cần nhiều cơ chế đảm bảo tính ổn định trong quá trình vận hành.
