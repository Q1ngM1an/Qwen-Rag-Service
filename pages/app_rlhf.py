import copy
import time

import streamlit as st
import uuid

from controller.rlhf_controller import RLHFController
from core.ui_utils import render_top_navbar, format_ai_message

# --- 页面配置 ---
st.set_page_config(page_title="RLHF 数据优化", page_icon="⚖️", layout="wide")
render_top_navbar()

st.markdown("""
    <style>
        .stMain {
           height: 100%
        }
    </style>
""", unsafe_allow_html=True)

# --- 初始化控制器 ---
ctrl = RLHFController()

# --- 状态管理 ---
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

current_session_id = st.session_state["session_id"]

default_rlhf_data = {
        "prompt": "",
        "answers": [None, None, None],
        "temperatures": [0.1, 0.7, 1.0],
        "winner": None
    }

if "rlhf_data" not in st.session_state:
    st.session_state["rlhf_data"] = copy.deepcopy(default_rlhf_data)

if "gen_id" not in st.session_state:
    st.session_state["gen_id"] = 0

data = st.session_state["rlhf_data"]

# --- 侧边栏：会话管理 (逻辑复用) ---
with st.sidebar:
    # # ===== 模型选择 =====
    available_models = ["qwen_0.6b", "qwen_32b"]  # 示例模型列表
    selected_model = st.selectbox(
        "🧠 选择模型",
        options=available_models,
        index=0,  # 默认选第一个
        help="选择你希望 AI 使用的语言模型"
    )

    st.header("🗂️ 偏好会话集")
    if st.button("➕ 新建偏好会话", use_container_width=True, type="primary"):
        ctrl.create_new_session()

    st.divider()

    st.subheader("🛠️ 工具")
    current_sid = st.session_state["session_id"]
    chat_data = ctrl.export_session_to_text(current_sid)
    st.download_button(
        label="📥 导出当前会话 (.txt)",
        data=chat_data,
        file_name=f"rlhf_chat_{current_sid[:8]}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.divider()

    sessions = ctrl.get_sidebar_sessions()
    if not sessions:
        st.caption("暂无历史记录")

    for s in sessions:
        col1, col2 = st.columns([5, 1])
        with col1:
            is_active = (s["id"] == current_session_id)
            # 按钮无法直接高亮，用 emoji 或 粗体 区分
            label = f"{'🔹 ' if is_active else ''}{s['title']}"
            if st.button(label, key=f"sess_{s['id']}", use_container_width=True):
                st.session_state["session_id"] = s["id"]
                # 切换会话时，清空当前的生成状态
                st.session_state["rlhf_data"] = copy.deepcopy(default_rlhf_data)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{s['id']}", help="删除"):
                ctrl.delete_session(s["id"])

# --- 主界面 ---
st.title("⚖️ RLHF 偏好收集")
st.caption(f"当前会话 ID: {current_session_id}")

# 1. 历史记录折叠栏 (Review Context)
history_msgs = ctrl.get_session_history(current_session_id)
if history_msgs:
    with st.expander(f"📜 回顾上下文 ({len(history_msgs)} 条消息)", expanded=False):
        for msg in history_msgs:
            role = "user" if msg.get("type") == "human" else "assistant"
            content = msg.get("data", {}).get("content") or msg.get("content", "")
            with st.chat_message(role):
                if role == "assistant":
                    format_ai_message(content)
                else:
                    st.markdown(content)

else:
    st.info("👋 这是一个新会话，暂无历史上下文。")

st.divider()

# 2. 输入区域
# 如果还没有生成，或者已经完成了上一轮选择（winner不为空），则允许输入
input_enabled = (data["prompt"] == "" or data["winner"] is not None)

if input_enabled:
    placeholder_text = "输入指令，生成三个版本的回答..." if data["winner"] is None else "本轮已结束，请输入新指令开启下一轮..."
    new_prompt = st.chat_input(placeholder_text)

    if new_prompt:
        st.session_state["rlhf_data"]["prompt"] = new_prompt
        st.session_state["rlhf_data"]["answers"] = [None, None, None]
        st.session_state["rlhf_data"]["winner"] = None
        st.session_state["gen_id"] += 1
        st.rerun()

# 3. 生成与对比区域
if data["prompt"]:
    st.info(f"正在评估问题：**{data['prompt']}**")

    # 工具栏
    col_tools, _ = st.columns([2, 8])
    with col_tools:
        if st.button("🔄 全部重生成", use_container_width=True, disabled=(data["winner"] is not None)):
            data["answers"] = [None, None, None]
            st.session_state["gen_id"] += 1
            st.rerun()

    cols = st.columns(3, gap="medium")

    for i, col in enumerate(cols):
        with col:
            temp = data["temperatures"][i]
            st.markdown(f"### 方案 {chr(65 + i)}")
            st.caption(f"Temperature: `{temp}`")

            with st.container(border=True):
                # 这里的 placeholder 配合下面的 empty() 和 sleep() 是消除残影的关键
                content_placeholder = st.empty()

                if data["answers"][i] is None:
                    # === 正在生成 ===
                    content_placeholder.empty()
                    time.sleep(0.05)  # 强制刷新帧，消除残影

                    with st.spinner("思考中..."):
                        stream = ctrl.generate_candidate_stream(data["prompt"], current_session_id, temp, selected_model="qwen_32b")
                        # 实时流式输出到占位符
                        full_res = content_placeholder.write_stream(stream)
                        # 生成完毕，回填状态
                        data["answers"][i] = full_res
                else:
                    # === 已有答案 ===
                    content_placeholder.markdown(data["answers"][i])

            # 按钮逻辑
            if data["winner"] is None:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✅ 接受", key=f"acc_{i}", use_container_width=True):
                        # 1. 获取本次 Prompt 对应的文档列表
                        context_text = ctrl.retrieve_context_text(data["prompt"])

                        print("-----------------------")
                        print(context_text)
                        print("-----------------------")

                        # 2. 保存偏好数据 (rlhf_feedback)
                        ctrl.save_preference(current_session_id, data["prompt"], data["answers"], data["temperatures"], i, context_text)
                        # 3. 将赢家写入对话历史 (chat_history) 实现多轮
                        ctrl.commit_interaction(current_session_id, data["prompt"], data["answers"], i)

                        data["winner"] = i
                        st.balloons()
                        st.rerun()
                with b2:
                    if st.button("🔄 重写", key=f"reg_{i}", use_container_width=True):
                        data["answers"][i] = None
                        st.rerun()
            else:
                # 结果展示
                if data["winner"] == i:
                    st.success("🎉 已选定此方案")
                else:
                    st.empty()  # 占位