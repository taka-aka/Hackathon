import sys
import os
# --- パス設定の修正 ---
# このファイル（app.pyなど）がある場所の親フォルダ（src）を自動的に取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# もしこのファイルが src の中にあるなら、そのパスを append する
if current_dir not in sys.path:
    sys.path.append(current_dir)

# もし構造上、一つ上の階層をパスに入れる必要がある場合はこちら：
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)
# ---------------------

import streamlit as st
import requests
from datetime import datetime

# st.sesson_state.messagesを保存、保存ファイルの読み込み用
from hackathon_app.frontend.save_load import save_chat, load_chat, reset_chat
from hackathon_app.frontend.ui.ui_settings import MINUTES_API_URL, CHAT_API_URL, PAGE_CONFIG, CSS
from hackathon_app.frontend.ui.ui_rendering_typing import render_message, buddy_typing
from hackathon_app.frontend.ui.ui_calendar import select_reminder
from hackathon_app.frontend.ui.ui_rooms import init_rooms, get_current_room, create_new_room, switch_room, rename_room, delete_room, reset_current_room

st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS, unsafe_allow_html=True)

if "minutes" not in st.session_state:
    st.session_state.minutes = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "show_minutes" not in st.session_state:
    st.session_state.show_minutes = False


init_rooms()
room = get_current_room()
# --- 仮CSS追加 ---
CUSTOM_BUTTON_CSS = """
<style>
/* 編集ボタンを小さく目立たなくする */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background-color: transparent;
    border: none;
    color: #888; /* グレーにして目立たなくする */
    font-size: 12px;
    padding: 0;
    height: auto;
    float: right;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    color: #ff4b4b; /* ホバー時だけ色を変える */
    background-color: transparent;
}
</style>
"""
st.markdown(CUSTOM_BUTTON_CSS, unsafe_allow_html=True)
# --- メイン画面: 履歴表示 (現在のルームのみ) ---
for idx, message in enumerate(room["messages"]):
    avatar = "👤" if message["role"] == "user" else "😎"
    time_str = message.get("time", "")

    with st.chat_message(message["role"], avatar=avatar):
        # 編集状態を管理するキー
        edit_key = f"edit_active_{idx}"
        
        # 1. 通常表示モード
        if not st.session_state.get(edit_key, False):
            render_message(message["content"], time_str)
            
            # ユーザーのメッセージのみ編集ボタンを表示（お好みでAssistant側も出せます）
            if message["role"] == "user":
                if st.button("✏️ 編集", key=f"btn_edit_{idx}"):
                    st.session_state[edit_key] = True
                    st.rerun()
        
        # 2. 編集モード（テキストエリアを表示）
        else:
            new_content = st.text_area(
                "メッセージを編集", 
                value=message["content"], 
                key=f"input_edit_{idx}"
            )
            
            col1, col2 = st.columns([1, 4]) # 保存ボタンを左に寄せる
            with col1:
                if st.button("💾 保存", key=f"save_{idx}", type="primary"):
                    room["messages"][idx]["content"] = new_content
                    save_chat(room["messages"]) # ファイルへ保存
                    st.session_state[edit_key] = False # 編集モード終了
                    st.rerun()
            with col2:
                if st.button("❌ キャンセル", key=f"cancel_{idx}"):
                    st.session_state[edit_key] = False
                    st.rerun()
        
# --- チャット入力 ---
if prompt := st.chat_input("メッセージを入力"):
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    room["messages"].append({"role": "user", "content": prompt, "time": current_time})
    save_chat(room["messages"]) #会話を保存
    with st.chat_message("user", avatar="👤"):
        render_message(prompt, current_time)

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

    buddy_typing(response_text)
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    room["messages"].append({"role": "assistant", "content": response_text, "time": current_time})
    save_chat(room["messages"])

# --- サイドバー ---
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if room["messages"]: 
            st.session_state.show_minutes = False # リセット 

            with st.spinner("整理してるよ..."):
                try:
                    payload = {"messages": room["messages"]}
                    res = requests.post(MINUTES_API_URL, json=payload, timeout=120)
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
        select_reminder(st.session_state.events)   
    
    if st.button("🔄会話リセット"):
        reset_current_room()

    st.write("---")
    st.write("チャット")
    if st.button("➕ 新しいチャットを作成", use_container_width=True):
        create_new_room()
    for r_name in st.session_state.rooms.keys():
        is_active = (st.session_state.current_room == r_name)
        if st.button(
            r_name,
            key=f"select_{r_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            switch_room(r_name)
    
        with st.expander(f"{r_name}の設定"):
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
                rename_room(r_name, new_name)
                st.rerun()

            # ガイドを表示
            if is_changed:
                st.caption("⚠️ [名前を変更]ボタンで保存")
            else:
                st.caption("名前を編集してください")

            st.write("---")
            delete_room(r_name)
