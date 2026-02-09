import re

import streamlit as st
import streamlit.components.v1 as components


def render_top_navbar():
    """
    渲染顶部导航栏 (JavaScript ID 注入版 - 绝对稳健)
    """

    # 1. CSS 样式：直接针对 ID #sticky-navbar 进行定义，不用再写复杂的层级选择器了
    # st.markdown("""
    #     <style>
    #         /* 隐藏 Header */
    #         header[data-testid="stHeader"] { visibility: hidden; }
    #
    #         /* 针对我们手动注入的 ID 进行样式设置 */
    #         #sticky-navbar {
    #             position: fixed;
    #             top: 0;
    #             left: 0;
    #             width: 100vw;
    #             z-index: 999999;
    #             background-color: white;
    #             box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    #             height: 5rem;
    #
    #             /* 内部布局居中 */
    #             display: flex;
    #             justify-content: center;
    #             align-items: center;
    #             padding-top: 1rem;
    #             padding-bottom: 0.5rem;
    #
    #             /* 强制覆盖 Streamlit 可能添加的边框 */
    #             border: none !important;
    #         }
    #
    #         /* 正文下移 */
    #         section[data-testid="stAppScrollToBottomContainer"] .block-container {
    #             padding-top: 6rem !important;
    #         }
    #
    #         /* 侧边栏层级调整 */
    #         div[data-testid="stSidebarCollapsedControl"] {
    #            top: 5.5rem
    #         }
    #
    #         .stSidebar {
    #            top: 5.5rem;
    #            /* 高度 = 屏幕总高 - 顶部偏移量 */
    #            height: calc(100vh - 6.3rem) !important;
    #
    #            /* 确保侧边栏内部滚动条能正确显示 */
    #            overflow-y: auto !important;
    #         }
    #     </style>
    # """, unsafe_allow_html=True)

    # 2. 渲染内容容器
    # 这个 container 会生成一个 stVerticalBlockBorderWrapper
    with st.container():
        # 你的导航栏按钮布局
        _, col1, col2, col3, col4, _ = st.columns([3, 1, 1, 1, 1, 3], gap="small")
        with col1:
            st.page_link("home.py", label="🏠 首页", use_container_width=True)
        with col2:
            st.page_link("pages/app_qa.py", label="🤖 智能问答", use_container_width=True)
        with col3:
            st.page_link("pages/app_rlhf.py", label="⚖️ 偏好收集", use_container_width=True)
        with col4:
            st.page_link("pages/app_file_uploader.py", label="📂 知识库", use_container_width=True)

    # # 3. JavaScript 注入：找到刚才那个容器，强行给它加个 ID
    # # 注意：这段代码会在 iframe 中运行，所以需要 window.parent 来操作主页面
    # js_code = """
    # <script>
    #     function setNavbarId() {
    #         // 找到主内容区域
    #         const mainBlock = window.parent.document.querySelector('.stMain .block-container');
    #         if (mainBlock) {
    #             // 找到第一个子元素 (这就是我们的 navbar 容器)
    #             // 根据你的截图，它是 stVerticalBlockBorderWrapper
    #             const firstChild = mainBlock.querySelector('div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"]');
    #
    #             if (firstChild) {
    #                 firstChild.id = 'sticky-navbar'; // 盖章！
    #                 console.log("Navbar ID set successfully!");
    #             } else {
    #                 // 如果没找到，可能页面还没渲染完，重试一下
    #                 setTimeout(setNavbarId, 50);
    #             }
    #         }
    #     }
    #     // 立即执行
    #     setNavbarId();
    # </script>
    # """
    # components.html(js_code, height=0, width=0)



# --- 视图辅助层 (View Helper) ---
def format_ai_message(content: str):
    """
    解析 <think> 标签并渲染为折叠框
    """
    think_pattern = r'(?:<think>)?(.*?)</think>(.*)'
    match = re.search(think_pattern, content, re.DOTALL)

    if match:
        think_content = match.group(1).strip()
        answer_content = match.group(2).strip()

        # 1. 渲染思考过程 (使用 expander 折叠)
        with st.expander("💭 AI 思考过程", expanded=False):
            st.markdown(think_content)

        # 2. 渲染最终回答
        st.markdown(answer_content)
    else:
        # 没有思考标签，直接显示
        st.markdown(content)
