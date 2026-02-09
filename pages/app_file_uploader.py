import time

import streamlit as st
from pypdf import PdfReader

from core.knowledge_base_service import KnowledgeBaseService
from core.ui_utils import render_top_navbar

st.set_page_config(page_title="知识库管理", layout="wide")
render_top_navbar()

# 初始化session_state
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "selected_files" not in st.session_state:
    st.session_state.selected_files = set()  # 存储选中的文件名
if "last_upload_success" not in st.session_state:
    st.session_state.last_upload_success = None  # 存储上次上传的成功信息

# 侧边栏导航
with st.sidebar:
    st.title("📚 知识库管理")
    st.divider()

    # 导航选项
    page = st.radio(
        "功能导航",
        ["📤 文件上传", "📋 文件列表"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("知识库文档管理系统")

# 根据选择的页面显示不同内容
if page == "📤 文件上传":
    # 文件上传页面
    st.title("📤 知识库文件上传")

    # 使用session_state来管理上传的文件
    if "upload_timestamp" not in st.session_state:
        st.session_state.upload_timestamp = str(time.time())


    # file_uploader - 支持多文件上传
    uploaded_files = st.file_uploader(
        "请上传文件（支持TXT和PDF格式）",
        type=['txt', 'pdf'],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.upload_timestamp}"
    )
    # 如果有新文件被选择，清除之前的成功消息
    if uploaded_files and len(uploaded_files) > 0:
        if st.session_state.last_upload_success:
            st.session_state.last_upload_success = None
            st.rerun()

    # 显示上次上传成功的消息（如果有的话）
    if st.session_state.last_upload_success:
        st.success(st.session_state.last_upload_success)
        # 提供清除消息的按钮
        if st.button("确定"):
            st.session_state.last_upload_success = None
            st.rerun()

    if uploaded_files and len(uploaded_files) > 0:
        if st.button("开始处理所有文件", type="primary"):
            success_count = 0
            processed_files = []
            for uploaded_file in uploaded_files:
                with st.expander(f"处理: {uploaded_file.name}", expanded=False):
                    try:
                        # 根据文件类型处理文件内容
                        text = ""
                        if uploaded_file.name.lower().endswith('.txt'):
                            text = uploaded_file.getvalue().decode("utf-8", errors='ignore')
                        elif uploaded_file.name.lower().endswith('.pdf'):
                            pdf_reader = PdfReader(uploaded_file)
                            for page in pdf_reader.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + "\n"

                        if not text.strip():
                            st.warning("文件内容为空")
                            continue

                        with st.spinner("载入知识库中..."):
                            result = st.session_state["service"].upload_by_str(text, uploaded_file.name)
                            st.success(f"{result}")
                            success_count += 1
                            processed_files.append(uploaded_file.name+":"+)

                    except Exception as e:
                        st.error(f"处理失败: {str(e)}")
            if success_count > 0:
                # 保存成功消息到session_state
                st.session_state.last_upload_success = f"✅ 完成！成功处理 {success_count}/{len(uploaded_files)} 个文件"
                if processed_files:
                    st.session_state.last_upload_success += f"\n\n已处理的文件：\n- " + "\n- ".join(processed_files)
                # 清空上传的文件列表
                st.session_state.upload_timestamp = str(time.time())
                time.sleep(1)
                st.rerun()  # 刷新页面以更新文件列表

else:
    # 文件列表页面
    st.title("📋 知识库文件列表")

    # 获取所有文档用于统计
    try:
        all_docs = st.session_state["service"].get_all_documents()
        filtered_docs = all_docs
        if st.session_state.search_query:
            filtered_docs = [
                doc for doc in all_docs
                if st.session_state.search_query.lower() in doc.get('source', '').lower()
            ]
    except Exception as e:
        all_docs = []
        filtered_docs = []
        st.error(f"加载文档失败: {str(e)}")

    # 搜索功能 - 在同一行显示
    search_container = st.container()
    with search_container:
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            search_query = st.text_input(
                "🔍 搜索文件名",
                value=st.session_state.search_query,
                placeholder="输入文件名关键词...",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("🔍 搜索", type="primary", use_container_width=True):
                st.session_state.search_query = search_query
                st.session_state.selected_files = set()  # 搜索时清空选中状态
                st.rerun()
        with col3:
            if st.button("🔄 重置", type="secondary", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.selected_files = set()  # 重置时也清空选中状态
                st.rerun()

    # 批量操作区域 - 一直显示
    batch_container = st.container()
    with batch_container:
        st.markdown("---")

        # 三列布局：选中信息、批量删除按钮、删除页面全部文件按钮
        batch_col1, batch_col2, batch_col3 = st.columns([2, 1, 1])

        with batch_col1:
            # 选中文件统计信息
            selected_count = len(st.session_state.selected_files)
            if selected_count > 0:
                st.info(f"📌 已选中 {selected_count} 个文件")
            else:
                st.info(f"📌 已选中 0 个文件")

        with batch_col2:
            # 批量删除按钮 - 如果没有选中文件则禁用
            if selected_count > 0:
                if st.button("🗑️ 批量删除", type="primary", use_container_width=True):
                    # 显示批量删除提示信息
                    st.warning(f"⚠️ 正在批量删除选中的 {selected_count} 个文件...")
                    # 执行批量删除
                    with st.spinner("正在批量删除文件..."):
                        deleted_count = 0
                        for filename in list(st.session_state.selected_files):
                            if st.session_state["service"].delete_document(filename):
                                deleted_count += 1
                                # 从选中集合中移除
                                st.session_state.selected_files.discard(filename)

                        if deleted_count > 0:
                            st.success(f"✅ 成功删除 {deleted_count} 个文件")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("批量删除失败")
            else:
                st.button("🗑️ 批量删除", disabled=True, use_container_width=True,
                          help="请先选择要删除的文件")

        with batch_col3:
            # 删除页面中全部文件按钮
            delete_all_label = "🗑️ 删除全部文件"
            if st.session_state.search_query:
                delete_all_label = f"🗑️ 删除搜索到文件"

            if st.button(delete_all_label, type="secondary", use_container_width=True,
                         help="删除当前页面显示的所有文件"):
                # 显示删除全部文件提示信息
                st.warning(f"⚠️ 正在删除当前页面显示的 {len(filtered_docs)} 个文件...")
                # 执行删除
                if len(filtered_docs) > 0:
                    with st.spinner("正在删除文件..."):
                        deleted_count = 0
                        for doc in filtered_docs:
                            filename = doc.get('source')
                            if filename and st.session_state["service"].delete_document(filename):
                                deleted_count += 1
                                # 从选中集合中移除（如果存在）
                                st.session_state.selected_files.discard(filename)

                        if deleted_count > 0:
                            st.success(f"✅ 成功删除 {deleted_count} 个文件")
                            # 清空搜索条件
                            st.session_state.search_query = ""
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("删除文件失败")
                else:
                    st.warning("当前页面没有可删除的文件")

        st.markdown("---")


    # 显示文件列表
    try:
        # 显示文件统计信息
        if st.session_state.search_query and len(filtered_docs) != len(all_docs):
            st.caption(f"📊 找到 {len(filtered_docs)} 个匹配文件（共 {len(all_docs)} 个文件）")
        else:
            st.caption(f"📊 共 {len(filtered_docs)} 个文件")

        if not filtered_docs:
            if st.session_state.search_query:
                st.warning(f"未找到包含 '{st.session_state.search_query}' 的文件")
            else:
                st.info("📭 知识库中没有文件")
        else:
            # 显示文件列表 - 使用紧凑布局
            st.markdown("---")

            for i, doc in enumerate(filtered_docs):
                # 创建一个紧凑的容器
                file_container = st.container()
                filename = doc.get('source', '未知文件')

                with file_container:
                    # 使用紧凑的列布局
                    file_col1, file_col2, file_col3, file_col4 = st.columns([1, 4, 3, 2])

                    with file_col1:
                        # 勾选框 - 从session_state获取选中状态
                        is_checked = filename in st.session_state.selected_files
                        checked = st.checkbox(
                            "111",
                            value=is_checked,
                            key=f"checkbox_{filename}_{i}",
                            label_visibility="collapsed"
                        )

                        # 处理勾选状态变化
                        if checked != is_checked:
                            if checked:
                                st.session_state.selected_files.add(filename)
                            else:
                                st.session_state.selected_files.discard(filename)
                            st.rerun()

                    with file_col2:
                        # 文件名显示，使用更紧凑的间距
                        st.markdown(f"**📄 {filename}**")

                    with file_col3:
                        create_time = doc.get('create_time', '未知时间')
                        # 使用更小的字体
                        st.markdown(f'<span style="font-size: 0.9em; color: #666;">🕐 {create_time}</span>',
                                    unsafe_allow_html=True)

                    with file_col4:
                        # 删除按钮
                        delete_key = f"delete_{filename}_{i}"
                        if st.button("🗑️ 删除", key=delete_key, type="secondary", use_container_width=True):
                            # 显示删除单个文件的提示信息
                            st.warning(f"⚠️ 正在删除文件: {filename}")
                            # 确认删除
                            if st.session_state["service"].delete_document(filename):
                                # 从选中集合中移除（如果存在）
                                st.session_state.selected_files.discard(filename)
                                st.success(f"已删除文件: {filename}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"删除文件失败: {filename}")

                # 使用更细的分隔线，减少间距
                if i < len(filtered_docs) - 1:  # 最后一个文件后不加分隔线
                    st.markdown('<hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #e0e0e0;">',
                                unsafe_allow_html=True)

    except Exception as e:
        st.error(f"加载文件列表失败: {str(e)}")

    # 添加一些自定义CSS来进一步调整间距
    st.markdown("""
    <style>
    /* 减少文件列表项的内边距 */
    .stContainer {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }

    /* 调整按钮的内边距 */
    .stButton > button {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
    }

    /* 调整搜索区域的间距 */
    div[data-testid="column"] {
        padding-top: 0.5rem;
    }

    /* 调整标题和内容之间的间距 */
    .stTitle {
        margin-bottom: 0.5rem !important;
    }

    /* 调整分割线的样式 */
    hr {
        margin: 0.5rem 0 !important;
    }

    /* 调整勾选框的样式 */
    .stCheckbox > label > div:first-child {
        margin-right: 0.5rem !important;
    }

    /* 批量操作区域样式 */
    .stInfo {
        padding: 0.5rem !important;
        margin-bottom: 0 !important;
    }

    /* 禁用按钮的样式 */
    .stButton > button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* 警告信息样式 */
    .stWarning {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
