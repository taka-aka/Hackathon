import streamlit as st
import requests
import time
import random
from datetime import datetime
import time
# backendフォルダを読み込めるようにパスを追加
from backend.summarize_chat import chat_with_llm # backendからインポート
# st.sesson_state.messagesを保存、保存ファイルの読み込み用
from save_load import save_chat, load_chat, reset_chat
from backend.add_reminder_to_google_calender import add_reminder

# --- 設定 ---
BACKEND_URL = "http://127.0.0.1:8000/generate_minutes"
CHAT_API_URL = "http://127.0.0.1:8000/chat"

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
    st.session_state.messages = load_chat()
    # st.session_state.messages = []
if "minutes" not in st.session_state:
    st.session_state.minutes = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "response_index" not in st.session_state:
    st.session_state.response_index = 0
if "show_minutes" not in st.session_state:
    st.session_state.show_minutes = False


# --- 【完全雑談】固定の返答リスト ---
# 誘導する言葉を一切排除し、日常の会話っぽくしています
# FIXED_BUDDY_RESPONSES = [
#     "おー、お疲れ！今日なんかあった？",
#     "マジか、それは予想外だわw",
#     "あーね。それめっちゃわかる気がする。",
#     "へぇ〜、それでその後どうなったん？",
#     "なるほど。まあ、なんとかなりそうじゃん！",
#     "いい感じだね。また後で詳しく教えてよ！"
# ]

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
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return full_response, current_time


def add_google_calender():
    events = st.session_state.events
    if events:
        st.success(f"予定が {len(events)}件 あったよ")
        eventlist = {
            f"{e['date']} {e['start_time']} {e['end_time']}: {e['title']}" : e
            for e in events
        }
        selected_event_keys =st.pills(
            label="追加したい予定を選択してね",
            options=list(eventlist.keys()),
            selection_mode="multi"
        )
        if st.button("📅 予定を反映"):
            if not selected_event_keys:
                st.warning("予定を選んでね！")
            else:
                selected_events = [eventlist[k] for k in selected_event_keys]
                add_reminder(selected_events)
                st.success("Googleカレンダーに追加したよ！🎉")


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
    save_chat(st.session_state.messages) #会話を保存
    with st.chat_message("user", avatar="👤"):
        # st.markdown(prompt)
        render_message(prompt, current_time)

    # # 固定の雑談返答
    # if st.session_state.response_index < len(FIXED_BUDDY_RESPONSES):
    #     response_text = FIXED_BUDDY_RESPONSES[st.session_state.response_index]
    #     st.session_state.response_index += 1
    # else:
    #     # リストを使い切ったら適当な相槌
    #     response_text = "うんうん、わかるよ。"
    
    # --- 修正ポイント：固定返答ではなくLLMを呼び出す ---
    with st.spinner(""):
        try:
            payload = {"messages": st.session_state.messages}
            res = requests.post(CHAT_API_URL, json=payload, timeout=30)
            if res.status_code == 200:
                response_text = res.json().get("response")
            else:
                response_text = "通信エラーになっちゃった。"
        except:
            response_text = "バックエンドが起動してないみたい。"

    final_text, current_time = buddy_typing(response_text)
    st.session_state.messages.append({"role": "assistant", "content": final_text, "time": current_time,})
    save_chat(st.session_state.messages) #会話を保存

# --- サイドバー ---
#議事録作成ボタンと会話リセットボタン
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        st.session_state.show_minutes = False
        if st.session_state.messages and not st.session_state.show_minutes: 
            # 会話データを送信  
            save_chat(st.session_state.messages)

            # # --- ここからデバッグ用表示 ---
            # st.write("### 📤 送信データ(デバッグ用)")
            # st.json(st.session_state.messages) # リスト形式を綺麗に表示します
            # # --- ここまで ---

            with st.spinner("整理してるよ..."):
                try:
                    payload = {"messages": st.session_state.messages}
                    res = requests.post(BACKEND_URL, json=payload, timeout=120)
                    if res.status_code == 200:
                        st.balloons()
                        st.session_state.minutes = res.json().get("minutes")
                        st.session_state.show_minutes = True
                        st.session_state.events = res.json().get("events", [])
                except:
                    st.error("バックエンドと通信できなかったよ。")
        else:
            st.warning("まだ何も話してないよ。")

    if st.session_state.show_minutes:
        st.markdown("### 📋 整理したメモ")
        st.info(st.session_state.minutes)
        st.download_button("メモを保存", st.session_state.minutes, "memo.txt")

        add_google_calender()        

    
    if st.button("🔄会話リセット"):
        # 過去の会話漏れセット
        reset_chat()
        st.session_state.messages = []
        st.rerun()
