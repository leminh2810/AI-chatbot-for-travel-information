import os
import sys
import streamlit as st
from dotenv import load_dotenv
from src.agent.agent_v1 import AgenticAgentV1  # <--- THÊM DÒNG NÀY

# 1. ĐỊNH TUYẾN ĐƯỜNG DẪN
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import các Module
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.core.fallback_provider import FallbackProvider
from src.core.local_provider import LocalProvider
from src.core.travel_tool import TravelTools
from src.core.chatbot.chatbot import BasicChatbot
from src.agent.agent import AgenticAgent

# =====================================================================
# 2. CẤU HÌNH GIAO DIỆN & SIDEBAR (MENU CHUYỂN ĐỔI)
# =====================================================================
st.set_page_config(page_title="Travel AI Assistant", page_icon="✈️", layout="wide")

st.sidebar.title("⚙️ Cấu hình Hệ thống")
st.sidebar.markdown("Dùng menu này để chuyển đổi và so sánh năng lực giữa các phiên bản AI.")

# Nút chọn chế độ
selected_mode = st.sidebar.radio(
    "Chọn phiên bản AI:",
    (
        "1. Baseline (Basic Chatbot)", 
        "2. ReAct Agent (V1 - Cơ bản)",   # <--- THÊM LỰA CHỌN NÀY
        "3. ReAct Agent (V2 - Nâng cao)"
    )
)

st.sidebar.divider()
st.sidebar.info(
    "💡 **Mẹo Demo:** Hãy thử hỏi câu: *'Tính doanh thu của Phú Quốc'* ở cả 2 chế độ để thấy Chatbot bị ảo giác (bịa số), còn Agent thì tính chính xác từ file CSV."
)

# =====================================================================
# 3. KHỞI TẠO PROVIDER (CHUNG CHO TẤT CẢ)
# =====================================================================
@st.cache_resource(show_spinner=False)
def get_llm_provider():
    load_dotenv()
    active_providers = []
    
    if os.getenv("GEMINI_API_KEY"):
        active_providers.append(GeminiProvider(model_name="gemini-1.5-flash"))
    if os.getenv("OPENAI_API_KEY"):
        active_providers.append(OpenAIProvider(model_name="gpt-4o-mini"))
        
    if len(active_providers) > 1:
        return FallbackProvider(active_providers)
    elif len(active_providers) == 1:
        return active_providers[0]
    else:
        return LocalProvider(model_name="llama3")

# =====================================================================
# 4. KHỞI TẠO BOT DỰA TRÊN CHẾ ĐỘ ĐÃ CHỌN
# =====================================================================
provider = get_llm_provider()

if "Baseline" in selected_mode:
    bot = BasicChatbot(provider=provider)
    st.title("🤖 Chatbot Cơ bản (Baseline)")
    st.caption("Chỉ trả lời dựa trên tệp trọng số có sẵn, không gọi công cụ, dễ bị ảo giác.")
elif "V1" in selected_mode:
    csv_file_path = os.path.join(project_root, "Data.csv")
    tools = TravelTools(csv_path=csv_file_path)
    bot = AgenticAgentV1(provider=provider, tools=tools, max_steps=5) # <--- KHỞI TẠO V1
    st.title("🧩 ReAct Agent (V1 - Cơ bản)")
    st.caption("Có vòng lặp ReAct nhưng dùng Regex đơn giản. Dễ bị kẹt vòng lặp nếu LLM sinh JSON sai.")
else:
    csv_file_path = os.path.join(project_root, "Data.csv")
    tools = TravelTools(csv_path=csv_file_path)
    bot = AgenticAgent(provider=provider, tools=tools, max_steps=5)
    st.title("🧠 ReAct Agent (V2 - Nâng cao)")
    st.caption("Có cơ chế Bullet-proof JSON Parsing và Self-Correction (tự sửa lỗi).")
# =====================================================================
# 5. QUẢN LÝ LỊCH SỬ TRÒ CHUYỆN (RESET KHI ĐỔI CHẾ ĐỘ)
# =====================================================================
# Nếu người dùng đổi chế độ, xóa lịch sử chat cũ đi để tránh lỗi context
if "current_mode" not in st.session_state:
    st.session_state.current_mode = selected_mode

if st.session_state.current_mode != selected_mode:
    st.session_state.messages = []
    st.session_state.current_mode = selected_mode

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": f"Hệ thống đã chuyển sang chế độ **{selected_mode}**. Tôi có thể giúp gì cho bạn?"
    }]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =====================================================================
# 6. XỬ LÝ GIAO TIẾP
# =====================================================================
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Đang xử lý bằng {selected_mode}..."):
            response = bot.run(prompt)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})