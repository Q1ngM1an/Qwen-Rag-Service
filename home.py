import streamlit as st

from core.ui_utils import render_top_navbar

st.set_page_config(page_title="首页", layout="wide")
render_top_navbar()

with st.container():
    # 你的导航栏按钮布局
    _, col, _ = st.columns([2, 3, 2], gap="small")
    with col:
        st.title("RAG 文档阅读助手")
        st.write("\n")
        st.write("\n")
        st.write("一个简单的RAG文档阅读助手！")
