import streamlit as st
import time, random

def  render_message(content: str, time_str: str):
    st.markdown(
        f"""
        <div style="font-size: 0.75em; color: #666; margin-bottom: 4px;">
            {time_str}
        </div>
        <div>
            {content}
        </div>
        """,
        unsafe_allow_html=True
    )


def buddy_typing(text):
    with st.chat_message("assistant", avatar="😎"):
        placeholder = st.empty()
        full_response = ""
        for char in text:
            full_response += char
            placeholder.markdown(full_response + "▌")
            # 友達がスマホを打つようなランダムな速さ
            time.sleep(random.uniform(0.02, 0.06))
        placeholder.markdown(full_response)
