import streamlit as st
import requests
import time
import random
from datetime import datetime

# st.sesson_state.messagesを保存、保存ファイルの読み込み用
from hackathon_app.frontend.save_load import save_chat, load_chat, reset_chat
from hackathon_app.frontend.ui.ui_settings import MINUTES_API_URL, CHAT_API_URL, PAGE_CONFIG, CSS
from hackathon_app.frontend.ui.ui_rendering_typing import render_message, buddy_typing
from hackathon_app.frontend.ui.ui_calendar import select_reminder
from hackathon_app.frontend.ui.ui_rooms import init_rooms, get_current_room, create_new_room, switch_room, rename_room, delete_room, reset_current_room

st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = load_chat()
if "minutes" not in st.session_state:
    st.session_state.minutes = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "show_minutes" not in st.session_state:
    st.session_state.show_minutes = False


init_rooms()
room = get_current_room()

# --- メイン画面: 履歴表示 (現在のルームのみ) ---
for message in room["messages"]:
    avatar = "👤" if message["role"] == "user" else "😎"

    time_str = message.get("time", "")

    with st.chat_message(message["role"], avatar=avatar):
        render_message(message["content"], time_str)
        
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

    final_text = buddy_typing(response_text)
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    room["messages"].append({"role": "assistant", "content": final_text, "time": current_time})
    save_chat(room["messages"])

# --- サイドバー ---
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if room["messages"]: 
            st.session_state.show_minutes = False # リセット 
            save_chat(st.session_state.messages)

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
        room["messages"] = []
        room["minutes"] = ""
        room["show_minutes"] = False
        reset_chat()
        st.rerun()

    st.write("---")
    st.write("チャット")
    if st.button("➕ 新しいチャットを作成", use_container_width=True):
        create_new_room()
    # ルーム一覧の描画
    for r_name in st.session_state.rooms.keys():
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            is_active = (st.session_state.current_room == r_name)
            if st.button(r_name, key=f"select_{r_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                switch_room(r_name)
        with col2:
            with st.popover(""):
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