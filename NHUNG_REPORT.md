# Báo Cáo Cá Nhân: Bài Thực Hành 3 - Chatbot vs Tác Nhân ReAct

- **Tên Sinh Viên**: Lương Thị Hồng Nhung
- **Mã Sinh Viên**: 2A202600811
- **Ngày**: 1/6/2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

*Mô tả đóng góp cụ thể của bạn vào codebase (ví dụ: triển khai công cụ cụ thể, sửa parser, v.v.)*

### Lớp 1: Giao Diện Người Dùng (Ứng Dụng Streamlit)
- **Các Mô-đun Được Triển Khai**: 
  - `app.py` - Điểm nhập chính của ứng dụng Streamlit
  - Các thành phần giao diện bao gồm cấu hình thanh bên, lựa chọn chế độ và quản lý giao diện chat

- **Điểm Nổi Bật Mã**:
  - **Cấu Hình Thanh Bên**: Tạo menu nút radio để lựa chọn giữa 3 chế độ AI (Chatbot Cơ Bản, ReAct V1, ReAct V2)
  - **Quản Lý Chế Độ**: Triển khai quản lý `st.session_state` để theo dõi chế độ hiện tại và đặt lại lịch sử chat khi thay đổi chế độ
  - **Lựa Chọn Nhà Cung Cấp LLM**: Triển khai hàm bộ nhớ đệm `get_llm_provider()` thông minh chọn giữa nhà cung cấp Gemini, OpenAI hoặc Fallback dựa trên khóa API có sẵn
  - **Hỗ Trợ Đa Chế Độ**: Kiến trúc hỗ trợ chuyển đổi giữa BasicChatbot và hai phiên bản Tác Nhân ReAct mà không cần khởi động lại
  - **Quản Lý Lịch Sử Chat**: Dòng 51-62 quản lý trạng thái phiên chat với logic đặt lại theo chế độ

- **Tài Liệu**: 
  - Lớp giao diện đóng vai trò là điểm điều phối cho toàn bộ hệ thống ReAct. Khi người dùng gửi truy vấn thông qua đầu vào Streamlit, nó sẽ định tuyến đến `BasicChatbot` hoặc `AgenticAgent` tùy thuộc vào lựa chọn thanh bên
  - Quản lý trạng thái phiên đảm bảo lịch sử chat được bảo tồn trong một chế độ nhưng bị xóa khi chuyển đổi, ngăn chặn nhầm lẫn về ngữ cảnh
  - Thanh bên cung cấp tính minh bạch vào cấu hình hệ thống, giúp người dùng hiểu nhà cung cấp LLM nào và phiên bản tác nhân nào đang hoạt động

---

### Lớp 4: Hệ Thống Đo Lường Từ Xa (Ghi Nhật Ký & Chỉ Số)
- **Các Mô-đun Được Triển Khai**:
  - `src/telemetry/logger.py` - Hệ thống ghi nhật ký sự kiện có cấu trúc
  - `src/telemetry/metrics.py` - Theo dõi chỉ số hiệu năng

- **Điểm Nổi Bật Mã**:
  - **Lớp IndustryLogger** (`logger.py`):
    - Triển khai ghi nhật ký sự kiện định dạng JSON để mô phỏng các thực hành công nghiệp
    - Tạo tệp nhật ký dựa trên ngày tháng ở định dạng `logs/YYYY-MM-DD.log`
    - Đầu ra kép: cả ghi nhật ký dựa trên tệp (JSON) và bảng điều khiển
    - Phương thức `log_event()` tiêu chuẩn hóa cấu trúc sự kiện với `timestamp`, loại `event` và tải trọng `data`
  
  - **Lớp LLMMetrics** (`metrics.py`):
    - Theo dõi `prompt_tokens`, `completion_tokens`, độ trễ và ước tính chi phí
    - Tính `token_ratio` (hoàn thành/nhắc nhở) để đo hiệu quả tạo đầu ra
    - Giá cả nhạy cảm nhà cung cấp (Gemini: $0,075/$0,30, Cục bộ: $0,0/$0,0)
    - Trả về từ điển dự liệu chỉ số có cấu trúc để ghi nhật ký
    - Thể hiện `metrics_tracker` toàn cầu để truy cập trên toàn mô-đun

- **Tài Liệu**:
  - **Tích Hợp với Vòng ReAct**: Trong `src/agent/agent.py` dòng 44-48, các chỉ số được ghi lại sau mỗi lệnh gọi LLM:
    ```
    start_time = metrics_tracker.start_timer()
    llm_output = self.provider.generate(self.system_prompt, agent_memory)
    latency = metrics_tracker.stop_timer(start_time)
    metrics = metrics_tracker.record_metrics(...)
    logger.log_event("LLM_METRIC", metrics)
    ```
  - **Loại Sự Kiện Được Ghi**: `AGENT_START`, `LOOP_STEP`, `LLM_METRIC`, `LLM_RESPONSE`, `TOOL_CALL`, `TOOL_OBSERVATION`, `PARSING_ERROR`, `AGENT_SUCCESS`, `AGENT_TIMEOUT`
  - Hệ thống đo lường từ xa cung cấp khả năng quan sát hoàn toàn về vòng lặp suy luận của tác nhân, cho phép phân tích và gỡ lỗi sau khi thực thi

---

## II. Trường Hợp Gỡ Lỗi (10 Điểm)

*Phân tích sự kiện thất bại cụ thể mà bạn gặp phải trong bài thực hành bằng hệ thống ghi nhật ký.*

### Vấn Đề Quan Trọng: Lỗi Phân Tích JSON với Các Ký Tự Tiếng Việt

- **Mô Tả Vấn Đề**: 
  Tác nhân liên tục không thể phân tích đầu ra JSON Action của riêng nó khi tạo lệnh gọi công cụ với tên địa điểm Tiếng Việt (ví dụ: "Phú Quốc"). Thông báo lỗi cho biết: `"Expecting ',' delimiter: line 1 column 76 (char 75)"`, khiến tác nhân hết thời gian sau 5 lần thất bại.

- **Nguồn Nhật Ký**: 
  Từ `logs/2026-06-01.log` (09:52:15 - 09:52:30):
  - `AGENT_START`: Truy vấn "DOANH THU CAO NHẤT Ở ĐỊA ĐIỂM NÀO"
  - Nhiều sự kiện `PARSING_ERROR` với lỗi giống hệt nhau ở vị trí cột 76
  - Tác nhân cố gắng sửa cú pháp JSON nhưng liên tục thất bại
  - Sự kiện cuối cùng: `AGENT_TIMEOUT` - "Max steps reached mà không có Final Answer"

- **Chẩn Đoán**: 
  Nguyên nhân gốc rễ là **vấn đề mã hóa ký tự với các ký tự Unicode Tiếng Việt trong phân tích JSON**. Khi Gemini LLM xuất các chuỗi Tiếng Việt (ví dụ: `"destination": "Hà Nội"`), bộ đếm vị trí ký tự của trình phân tích JSON đã tính sai do mã hóa UTF-8 đa byte. Một ký tự Tiếng Việt như "à" (3 byte) được tính là 1 ký tự, dịch chuyển vị trí dự kiến của dấu phẩy và gây ra lỗi phân tích. Các nỗ lực tự sửa của tác nhân cũng tạo ra đầu ra có lỗi giống hệt, tạo ra mô hình vòng lặp vô hạn.

  Vấn đề KHÔNG nằm ở dấu nhắc LLM hoặc thông số kỹ thuật công cụ—cả hai đều đúng—mà nằm ở cách Python `json.loads()` báo cáo vị trí ký tự cho các chuỗi Unicode. Tác nhân không thể tự chẩn đoán vấn đề thực tế vì thông báo lỗi gây hiểu nhầm.

- **Giải Pháp**: 
  Triển khai **phân tích JSON nhạy cảm với đa byte với logic thử lại** trong `src/agent/agent.py` (dòng 95-130):
  - Thêm vòng `MAX_RETRIES = 2` để cho phép LLM thử nhiều lần
  - Sử dụng `raw_action_text.find("{")` và `rfind("}")` để trích xuất ranh giới JSON, bỏ qua các vấn đề về vị trí ký tự
  - Bao bọc trích xuất trong try-except để bắt `json.JSONDecodeError` và cung cấp thông báo lỗi rõ ràng hơn
  - Khi phân tích JSON thất bại, tác nhân được nhắc lại với hướng dẫn rõ ràng: `"Yêu cầu chỉ xuất chuỗi JSON sạch, không có văn bản thừa"`
  - Thêm sự kiện `FATAL_ERROR` nếu vượt quá giới hạn thử lại, trả về thông báo lỗi thân thiện với người dùng
  
  **Kết Quả**: Sau khi triển khai, truy vấn tương tự lúc 10:35:05 và 10:45:26 đã thành công (AGENT_SUCCESS) với tỷ lệ token_ratio là 0,15-0,19, xác nhận rằng bản sửa lỗi giải quyết được vấn đề mã hóa ký tự Tiếng Việt.

---

## III. Cái Nhìn Sâu Sắc Cá Nhân: Chatbot vs ReAct (10 Điểm)

*Suy ngẫm về sự khác biệt về khả năng suy luận.*

1. **Suy Luận**: Khối `Thought` đã giúp tác nhân so với câu trả lời Chatbot trực tiếp như thế nào?
   - Khối `Thought` cung cấp **tính giải thích và minh bạch trong lập kế hoạch**. Trong các lần chạy tác nhân thành công (09:55:29, 10:15:31), tác nhân đã thể hiện suy luận đa bước:
     - Truy vấn: "Có bao nhiêu khách hàng đến Phú Quốc"
     - Suy nghĩ: "Tôi cần tìm tổng số lượng khách đến Phú Quốc"
     - Hành động: Gọi công cụ `calculate_destination_revenue` với tham số địa điểm
     - Suy luận rõ ràng này cho phép chúng tôi (thông qua ghi nhật ký) hiểu TẠI SAO tác nhân chọn một công cụ cụ thể, không chỉ là quyết định gì. Ngược lại, BasicChatbot chỉ xuất ra câu trả lời mà không có lý do—thường là những con số bịa ra khi không có quyền truy cập dữ liệu.
   
2. **Độ Tin Cậy**: Tác nhân thực sự hoạt động *tệ hơn* Chatbot trong những trường hợp nào?
   - **Tệ hơn: Xử lý các truy vấn mơ hồ/ngoài phạm vi**. Truy vấn lúc 10:16:03: "Có bao nhiêu khách hủy phòng?"
     - Tác nhân cố gắng kiểm tra các trạng thái đặt phòng riêng lẻ (B00001-B00005) tuần tự, đạt tối đa các bước (5) trước khi tìm thấy các đặt phòng bị hủy
     - Tác nhân trả lại: "Xin vui lòng cung cấp mã đặt phòng để..."—một câu trả lời không đầy đủ
     - BasicChatbot sẽ ngay lập tức tạo ra câu trả lời trực tiếp (có khả năng là bịa ra) mà không có độ trễ
   
   - **Tệ hơn: Độ bền với định dạng JSON**. Các lỗi phân tích (09:52-10:44) cho thấy tác nhân có thể trở nên **hoàn toàn không hoạt động** nếu LLM xuất JSON sai định dạng liên tục, trong khi BasicChatbot không bao giờ phụ thuộc vào phân tích đầu ra có cấu trúc.
   
   - **Tốt hơn: Độ chính xác trong các truy vấn hướng dữ liệu**. Đối với các truy vấn có cấu trúc như "doanh thu của Phú Quốc", Tác nhân luôn trả lại: "3.206.141.000 VNĐ, 1113 khách" (được xác minh từ nhật ký), trong khi BasicChatbot sẽ bịa ra những con số.

3. **Quan Sát**: Phản hồi từ môi trường (quan sát) đã ảnh hưởng đến các bước tiếp theo như thế nào?
   - Từ nhật ký lúc 10:15:31, sau khi quan sát: `{"destination": "Phú Quốc", "total_revenue_vnd": 3206141000.0, "total_pax_served": 1113}`, khối Suy Nghĩ của tác nhân ngay lập tức kết luận rằng nó có đủ thông tin và chuyển đến Câu Trả Lời Cuối Cùng mà không cần gọi công cụ không cần thiết
   - Ngược lại, truy vấn thất bại lúc 10:16:03 cho thấy tác nhân liên tục gọi `check_booking_status` với booking_ids tuần tự (B00001→B00005) mà không có tiêu chí lọc rõ ràng, gợi ý rằng **Phản hồi từ Quan Sát một mình không đủ để hướng dẫn lựa chọn công cụ chính xác mà không có logic lọc trước rõ ràng trong dấu nhắc**
   - Điều này làm nổi bật một lỗ hổng thiết kế chính: tác nhân cần (a) công cụ `list_all_cancelled_bookings`, hoặc (b) tham số tìm kiếm rõ ràng trong `check_booking_status`, thay vì lặp lại bằng vũ lực

---

## IV. Cải Tiến Trong Tương Lai (5 Điểm)

*Bạn sẽ mở rộng quy mô này cho hệ thống tác nhân AI cấp sản xuất như thế nào?*

- **Khả Năng Mở Rộng**: 
  - **Thực Thi Không Đồng Bộ**: Thay thế các lệnh gọi công cụ đồng bộ trong vòng lặp ReAct bằng `asyncio` hoặc hàng đợi tác vụ celery. Tắc nghẽn hiện tại: độ trễ API Gemini (2-3s mỗi lệnh gọi) × 5 bước tối đa = lên tới 15 giây mỗi truy vấn. Không đồng bộ sẽ song song hóa các lệnh gọi công cụ độc lập.
  - **Ghi Nhật Ký Phân Tán**: Di chuyển từ ghi nhật ký dựa trên tệp sang đo lường từ xa tập trung (ví dụ: ELK Stack, Datadog). `logs/YYYY-MM-DD.log` hiện tại sẽ phát triển không bền vững với lưu lượng cao; hệ thống tập trung cho phép cảnh báo theo thời gian thực về các loại `PARSING_ERROR`.
  - **Bộ Nhớ Đệm**: Thêm Redis/Memcached cho kết quả `calculate_destination_revenue` vì dữ liệu du lịch thay đổi hàng tuần, không phải mỗi yêu cầu.

- **An Toàn**:
  - **Tác Nhân Giám Sát LLM**: Triển khai LLM thứ cấp kiểm toán Câu Trả Lời Cuối Cùng của tác nhân so với dữ liệu Quan Sát gốc. Ví dụ: Tác nhân nói "3,2 tỷ VNĐ" → Giám sát xác thực rằng trường `total_revenue_vnd` thực sự chứa giá trị đó, ngăn chặn ảo giác sau khi thực thi công cụ.
  - **Quy Trình Phê Duyệt Công Cụ**: Đối với các hoạt động nhạy cảm (ví dụ: hủy đặt phòng), yêu cầu phê duyệt của con người giữa thực thi Lệnh Gọi Công Cụ và Quan Sát Công Cụ.
  - **Tinh Chỉnh Đầu Vào**: Xác thực các truy vấn người dùng để phòng chống các cuộc tấn công tiêm. Hệ thống hiện tại trực tiếp bao gồm đầu vào của người dùng trong bộ nhớ tác nhân mà không cần xác thực.

- **Hiệu Năng**:
  - **Nhúng & Truy Xuất Công Cụ**: Với 100+ công cụ, triển khai cơ sở dữ liệu vector (Pinecone/Weaviate) để truy xuất các công cụ liên quan về mặt ngữ nghĩa dựa trên truy vấn người dùng thay vì nhắc LLM với tất cả các công cụ. Điều này giảm tăng token dấu nhắc và độ trễ.
  - **Cắt Tỉa Suy Nghĩ**: Bộ nhớ đệm đầu ra `Thought` từ các truy vấn giống hệt/tương tự trước đó để bỏ qua giai đoạn suy luận, trao đổi độ chính xác để nhanh hơn (hữu ích cho các truy vấn tần suất cao).
  - **Tối Ưu Hóa Token**: Hệ thống hiện tại ghi nhật ký token dấu nhắc/hoàn thành đầy đủ. Trong sản xuất, triển khai ngân sách token: nếu truy vấn tiêu thụ >2000 token trong một lệnh gọi LLM, hãy kích hoạt fallback cho công cụ đơn giản hơn với ít bước suy luận hơn.
  - **Hiệu Năng Giao Diện**: Ứng dụng Streamlit hiện tại khởi tạo lại nhà cung cấp LLM mỗi khi tải lại trang. Sử dụng nhóm kết nối liên tục và luồng công nhân nền để xử lý các phiên người dùng đồng thời một cách hiệu quả.

---

> [!LƯU Ý]
> Gửi báo cáo này bằng cách đổi tên thành `REPORT_[TÊN_CỦA_BẠN].md` và đặt nó trong thư mục này.
