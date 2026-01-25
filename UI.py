import streamlit as st
import requests
import time
import random
from datetime import datetime
import time

# st.sesson_state.messagesを保存、保存ファイルの読み込み用
from save_load import save_chat, load_chat, reset_chat

# --- 設定 ---
BACKEND_URL = "http://127.0.0.1:8000/generate_minutes"

st.set_page_config(page_title="トーク", page_icon="💬")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #7494C0; }
    div[data-testid="stChatMessage"] { background-color: transparent !important; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) { flex-direction: row-reverse; text-align: right; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) div[data-testid="stMarkdownContainer"] {
        background-color: #8DE055; color: #000; padding: 10px 15px; border-radius: 15px 15px 2px 15px; display: inline-block; margin-right: 10px;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF; color: #000; padding: 10px 15px; border-radius: 15px 15px 15px 2px; display: inline-block; margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    # 過去の会話履歴を読み込む
        st.session_state.messages = load_chat()
    # st.session_state.messages = []
if "response_index" not in st.session_state:
    st.session_state.response_index = 0

# --- 【完全雑談】固定の返答リスト ---
# 誘導する言葉を一切排除し、日常の会話っぽくしています
FIXED_BUDDY_RESPONSES = [
    "おー、お疲れ！今日なんかあった？",
    "マジか、それは予想外だわw",
    "あーね。それめっちゃわかる気がする。",
    "へぇ〜、それでその後どうなったん？",
    "なるほど。まあ、なんとかなりそうじゃん！",
    "いい感じだね。また後で詳しく教えてよ！"
]

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
    # retrun full_response

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return full_response, current_time

# 履歴表示
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "😎"

    # 時間も表示
    time_str = message.get("time", "")

    with st.chat_message(message["role"], avatar=avatar):
        # st.markdown({message["content"]})
        render_message(message["content"], time_str)
        
# --- チャット入力 ---
if prompt := st.chat_input("メッセージを入力"):
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time,})
    with st.chat_message("user", avatar="👤"):
        # st.markdown(prompt)
        render_message(prompt, current_time)

    # 固定の雑談返答
    if st.session_state.response_index < len(FIXED_BUDDY_RESPONSES):
        response_text = FIXED_BUDDY_RESPONSES[st.session_state.response_index]
        st.session_state.response_index += 1
    else:
        # リストを使い切ったら適当な相槌
        response_text = "うんうん、わかるよ。"

    final_text, current_time = buddy_typing(response_text)
    st.session_state.messages.append({"role": "assistant", "content": final_text, "time": current_time,})

# --- サイドバー ---
#議事録作成ボタンと会話リセットぼたん
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if st.session_state.messages:
            # 会話データを送信  
            save_chat(st.session_state.messages)

            # --- ここからデバッグ用表示 ---
            st.write("### 📤 送信データ(デバッグ用)")
            st.json(st.session_state.messages) # リスト形式を綺麗に表示します
            # --- ここまで ---

            with st.spinner("整理してるよ..."):
                try:
                    payload = {"messages": st.session_state.messages}
                    res = requests.post(BACKEND_URL, json=payload, timeout=120)
                    if res.status_code == 200:
                        st.balloons()
                        st.markdown("### 📋 整理したメモ")
                        st.info(res.json().get("minutes"))
                        st.download_button("保存する", res.json().get("minutes"), "memo.txt")
                except:
                    st.error("バックエンドと通信できなかったよ。")
        else:
            st.warning("まだ何も話してないよ。")
            
    if st.button("🔄会話リセット"):
        # 過去の会話漏れセット
        reset_chat()

        st.session_state.messages = []
        st.session_state.response_index = 0
        st.rerun()