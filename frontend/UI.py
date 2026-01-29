import streamlit as st
import requests
import time
import random
from datetime import datetime
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

# --- 複数ルーム管理用の初期化 ---
if "rooms" not in st.session_state:
    st.session_state.rooms = {
        "トークルーム 1": {"messages": load_chat(), "minutes": "", "events": [], "show_minutes": False}
    }
if "current_room" not in st.session_state:
    st.session_state.current_room = "トークルーム 1"

# 現在のルームのデータを参照しやすくする
room = st.session_state.rooms[st.session_state.current_room]

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


# --- メイン画面: 履歴表示 (現在のルームのみ) ---
for message in room["messages"]:
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
    room["messages"].append({"role": "user", "content": prompt, "time": current_time})
    save_chat(room["messages"]) #会話を保存
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
            payload = {"messages": room["messages"]}
            res = requests.post(CHAT_API_URL, json=payload, timeout=30)
            if res.status_code == 200:
                response_text = res.json().get("response")
            else:
                response_text = "通信エラーになっちゃった。"
        except:
            response_text = "バックエンドが起動してないみたい。"

    final_text, current_time = buddy_typing(response_text)
    room["messages"].append({"role": "assistant", "content": final_text, "time": current_time})
    save_chat(room["messages"]) #会話を保存

# --- サイドバー ---
#議事録作成ボタンと会話リセットボタン
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if room["messages"]: 
            st.session_state.show_minutes = False # リセット 
            # 会話データを送信  
            save_chat(st.session_state.messages)

            # # --- ここからデバッグ用表示 ---
            # st.write("### 📤 送信データ(デバッグ用)")
            # st.json(st.session_state.messages) # リスト形式を綺麗に表示します
            # # --- ここまで ---

            with st.spinner("整理してるよ..."):
                try:
                    payload = {"messages": room["messages"]}
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
        room["messages"] = []
        room["minutes"] = ""
        room["show_minutes"] = False
        reset_chat()
        st.rerun()

    st.write("---")
    st.write("チャット")
    if st.button("➕ 新しいチャットを作成", use_container_width=True):
        # 重複しない名前を作る（現在の秒数などを利用）
        timestamp = datetime.now().strftime("%H%M%S")
        new_name = f"トークルーム {timestamp}"
        st.session_state.rooms[new_name] = {
            "messages": [], 
            "minutes": "", 
            "events": [], 
            "show_minutes": False
        }
        st.session_state.current_room = new_name
        st.rerun()

    # ルーム一覧の描画
    room_names = list(st.session_state.rooms.keys())
    
    for idx, r_name in enumerate(room_names):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            is_active = (st.session_state.current_room == r_name)
            if st.button(r_name, key=f"select_{r_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.current_room = r_name
                st.rerun()
        with col2:
            with st.popover(""):
                # --- 名前を編集機能 ---
                input_key = f"edit_name_input_{r_name}"

                # 現在表示されている名前を管理
                new_name = st.text_input(
                    "このチャットの名前を変更する", 
                    value=r_name, 
                    key=input_key
                )

                # 入力された名前が現在の名前と違う場合のみ、保存ボタンを表示（活性化）させる
                # strip() で空白のみの名前を防止
                is_changed = (new_name != r_name and new_name.strip() != "")

                if st.button(
                    "✅ 名前を変更", 
                    key=f"rename_btn_{r_name}", 
                    use_container_width=True,
                    disabled=not is_changed # 変更がない場合は押せない
                ):
                    # 順序を維持して辞書を再構築
                    old_name = r_name
                    final_name = new_name.strip()
                    
                    new_rooms = {}
                    for k in st.session_state.rooms.keys():
                        if k == old_name:
                            new_rooms[final_name] = st.session_state.rooms[old_name]
                        else:
                            new_rooms[k] = st.session_state.rooms[k]
                    
                    st.session_state.rooms = new_rooms
                    if st.session_state.current_room == old_name:
                        st.session_state.current_room = final_name
                    
                    st.rerun()

                # ガイドを表示
                if is_changed:
                    st.caption("⚠️ [名前を変更]ボタンで保存")
                else:
                    st.caption("名前を編集してください")

                st.write("---")
                
                # --- 削除機能 (二重確認付き) ---
                confirm_key = f"confirm_del_{r_name}"
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False

                if not st.session_state[confirm_key]:
                    # 最初の削除ボタン
                    if st.button("🗑️ 削除", key=f"del_btn_{r_name}", use_container_width=True):
                        if len(st.session_state.rooms) > 1:
                            st.session_state[confirm_key] = True
                            st.rerun()
                        else:
                            warning_placeholder = st.empty()
                            warning_placeholder.warning("最後のルームは削除できません")
                            # 3秒待機
                            time.sleep(1)
                            # 警告を消去
                            warning_placeholder.empty()
                            # 画面の状態をリセットするためにリロード
                            st.rerun()
                else:
                    # 二重確認画面 (サイドバーの制約により列を使わず縦に配置)
                    st.error(f"本当に「{r_name}」を削除しますか？")
                    
                    if st.button("✅ 削除する", key=f"yes_{r_name}", use_container_width=True, type="primary"):
                        del st.session_state.rooms[r_name]
                        # 削除したルームを選択していたら移動
                        if st.session_state.current_room == r_name:
                            st.session_state.current_room = list(st.session_state.rooms.keys())[0]
                        
                        # 確認フラグを削除
                        if confirm_key in st.session_state:
                            del st.session_state[confirm_key]
                        st.rerun()
                        
                    if st.button("❌ キャンセル", key=f"no_{r_name}", use_container_width=True):
                        st.session_state[confirm_key] = False
                        st.rerun()