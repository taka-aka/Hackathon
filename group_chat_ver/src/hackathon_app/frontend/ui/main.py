import streamlit as st
import requests
from datetime import datetime

from hackathon_app.backend.database import init_db
init_db()
from hackathon_app.frontend.ui.ui_settings import MINUTES_API_URL, CHAT_API_URL, ROOMS_API_URL, PAGE_CONFIG, CSS
from hackathon_app.frontend.ui.ui_rendering import render_message
from hackathon_app.frontend.ui.ui_calendar import select_reminder
from hackathon_app.frontend.ui.ui_rooms import init_rooms, load_room_messages, save_room_messages, create_new_room, switch_room, rename_room, delete_room, reset_current_room
from hackathon_app.frontend.ui.ui_login import init_username

st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS, unsafe_allow_html=True)

if "minutes" not in st.session_state:
    st.session_state.minutes = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "show_minutes" not in st.session_state:
    st.session_state.show_minutes = False

rooms = init_rooms() # (st.session_state) current_room_id, current_room_name を取得

current_room_id = int(st.session_state.current_room_id)
current_room_name = st.session_state.current_room_name
if "messages" not in st.session_state:
    # user_id, username, avatar, content, time を取得
    st.session_state.messages = load_room_messages(current_room_id)

init_username() # (st.session_state) user_id, username, avatar を取得

for msg in st.session_state.messages:
    is_me = (msg["user_id"] == st.session_state.user_id)

    with st.chat_message(
        "user" if is_me else "assistant",
        avatar=msg["avatar"]
    ):
        render_message(msg, is_me, msg["time"])
        
# --- チャット入力 ---
if prompt := st.chat_input("メッセージを入力"):
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    st.session_state.messages.append({
        "user_id": st.session_state.user_id,
        "username": st.session_state.username,
        "avatar": st.session_state.avatar,
        "content": prompt,
        "time": current_time
    })
    save_room_messages(current_room_id, st.session_state.messages) #会話を保存
    st.rerun()


    # with st.chat_message("user", avatar="👤"):
        # render_message(prompt, current_time)

    # with st.spinner("通信中..."):
    #     try:
    #         payload = {"messages": st.session_state.messages}
    #         res = requests.post(CHAT_API_URL, json=payload, timeout=30)
        
    #         if res.status_code == 200:
    #             response_text = res.json().get("response")
    #         else:
    #             # バックエンドから返ってきたエラー詳細を表示
    #             error_detail = res.json().get('detail', '不明なエラー')
    #             response_text = f"サーバーエラー ({res.status_code}): {error_detail}"
    #             print(f"DEBUG: Server Error: {res.text}")
            
    #     except requests.exceptions.ConnectionError:
    #         response_text = "サーバーに接続できません。バックエンドが起動しているか確認してください。"
    #     except Exception as e:
    #         response_text = f"フロントエンドで例外発生: {str(e)}"
    #         print(f"DEBUG: Exception: {e}")
            
    # buddy_typing(response_text)
    # now = datetime.now()
    # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # st.session_state.messages.append({"role": "assistant", "content": response_text, "time": current_time})
    # save_room_messages(current_room_id, st.session_state.messages)

# --- サイドバー ---
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if st.session_state.messages: 
            st.session_state.show_minutes = False # リセット 

            with st.spinner("整理してるよ..."):
                try:
                    
                    payload = {"messages": st.session_state.messages}
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
        reset_current_room(current_room_id)

    st.write("---")
    st.write("ルーム選択")
    if st.button("➕ 新しいチャットを作成", use_container_width=True):
        create_new_room()

    for room_id, room_name in rooms.items():
        is_active = (current_room_id == int(room_id))
        if st.button(
            room_name,
            key=f"select_{room_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            switch_room(room_name, room_id)

        with st.expander(f"{room_name}の設定"):
            input_key = f"edit_name_input_{room_name}"

            # 現在表示されている名前を管理
            new_name = st.text_input(
                "このチャットの名前を変更する", 
                value=room_name, 
                key=input_key
            )

            is_not_empty = new_name.strip() != ""
            is_not_duplicate = new_name not in rooms.values()
            is_changed = (new_name != room_name and is_not_empty and is_not_duplicate)

            if st.button(
                "✅ 名前を変更", 
                key=f"rename_btn_{room_id}", 
                use_container_width=True,
                disabled=not is_changed # 変更がない場合は押せない
            ):
                # 順序を維持して辞書を再構築
                rename_room(room_name, new_name.strip())

            # ガイドを表示
            if not is_not_empty:
                st.caption("名前を空にすることはできません")
            elif not is_not_duplicate:
                st.caption("⚠️ 他のルーム名と重複しています")
            elif is_changed:
                st.caption("⚠️ [名前を変更]ボタンで保存")
            else:
                st.caption("名前を編集してください")

            st.write("---")
            delete_room(room_name, int(room_id))
