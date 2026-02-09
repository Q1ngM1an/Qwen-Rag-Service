import re
import uuid

import streamlit as st

from controller.qa_controller import QAChatController
from core.ui_utils import render_top_navbar, format_ai_message

# 设置页面配置
st.set_page_config(
    page_title="AI智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
render_top_navbar()

st.markdown("""
    <style>
        .stMain {
           height: 100%
        }
    </style>
""", unsafe_allow_html=True)

ctrl = QAChatController()

# 1. 初始化 Session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

current_session_id = st.session_state["session_id"]

# 2. 侧边栏：历史记录
with st.sidebar:
    # # ===== 模型选择 =====
    available_models = ["qwen_0.6b", "qwen_32b"]  # 示例模型列表
    selected_model = st.selectbox(
        "🧠 选择模型",
        options=available_models,
        index=0,  # 默认选第一个
        help="选择你希望 AI 使用的语言模型"
    )

    st.header("🗂️ 历史会话")
    if st.button("➕ 新建对话", use_container_width=True, type="primary"):
        ctrl.create_new_session()

    st.divider()

    # 2. 导出功能 (新增)
    st.subheader("🛠️ 工具")
    current_sid = st.session_state["session_id"]
    chat_data = ctrl.export_session_to_text(current_sid)
    st.download_button(
        label="📥 导出当前会话 (.txt)",
        data=chat_data,
        file_name=f"chat_{current_sid[:8]}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.divider()

    # 获取并显示列表
    sessions = ctrl.get_sidebar_sessions()
    if not sessions:
        st.caption("暂无历史记录")

    for s in sessions:
        # 布局：左边标题按钮，右边删除按钮
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(f"💬 {s['title']}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state["session_id"] = s["id"]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{s['id']}", help="删除"):
                ctrl.delete_session(s["id"])

# 3. 主界面标题
st.title("🤖 RAG 智能问答助手")
st.caption(f"当前会话 ID: {current_session_id}")
st.divider()

# 4. 渲染历史消息 (从 SQLite 加载)
# 注意：RagService 的 RunnableWithMessageHistory 会自动存，我们只需要读
messages = ctrl.get_session_history(current_session_id)

# 如果是新会话，messages 为空，显示欢迎语
if not messages:
    st.chat_message("assistant").write("你好！我是你的 AI 助手，请问有什么可以帮你？")

for msg in messages:
    # msg 是字典: {'type': 'human'/'ai', 'data': {'content': '...'}}
    # 或者是 LangChain 序列化后的结构
    role = "user" if msg.get("type") == "human" else "assistant"
    content = msg.get("data", {}).get("content", "")

    with st.chat_message(role):
        if role == "assistant":
            format_ai_message(content)
        else:
            st.markdown(content)

# 5. 处理用户输入
# --- 输入与生成逻辑 ---
prompt = st.chat_input("请输入您的问题...")

# 处理重新生成 (通过 Session State 标记)
if "trigger_regenerate" in st.session_state and st.session_state["trigger_regenerate"]:
    # 既然是重新生成，Prompt 应该是之前的最后一条用户消息
    # 我们在 controller.regenerate_last_response 已经处理了删除 AI 消息
    # 这里只需要拿到之前的 User Prompt
    prompt = st.session_state["regenerate_prompt"]
    # 消费掉这个 flag
    del st.session_state["trigger_regenerate"]
    del st.session_state["regenerate_prompt"]

if prompt:
    if "is_regenerating" not in st.session_state:
        with st.chat_message("user"):
            st.write(prompt)
    else:
        # 是重新生成，界面上已经有 User 消息了，不需要再 print
        del st.session_state["is_regenerating"]

    # 生成逻辑
    with st.chat_message("assistant"):
        container = st.empty()
        full_response = ""
        stream = ctrl.generate_response_stream(prompt, current_sid, selected_model)

        for chunk in stream:
            # ... chunk 处理 ...
            full_response += chunk
            container.markdown(full_response + "▌")

        container.markdown(full_response)  # 最终显示

        st.rerun()  # 刷新以更新历史记录并显示按钮

# --- 在所有消息渲染完的最下方，显示“重新生成”按钮 ---
# 只有当最后一条消息是 AI 发的时，才允许重新生成
if messages and (messages[-1].get("type") == "ai" or messages[-1].get("role") == "assistant"):
    col_regen, _ = st.columns([2, 8])
    with col_regen:
        if st.button("🔄 对回答不满意？重新生成", use_container_width=True):
            last_user_prompt = ctrl.regenerate_last_response(current_sid)  # 这里只删了 AI

            if last_user_prompt:
                st.session_state["trigger_regenerate"] = True
                st.session_state["regenerate_prompt"] = last_user_prompt
                st.session_state["is_regenerating"] = True  # 标记位，防止重复显示 User 气泡
                st.rerun()