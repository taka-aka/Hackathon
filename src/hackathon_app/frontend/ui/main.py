import streamlit as st
import requests
from datetime import datetime

from hackathon_app.backend.database import init_db
init_db()
from hackathon_app.frontend.ui.ui_settings import MINUTES_API_URL, CHAT_API_URL, ROOMS_API_URL, PAGE_CONFIG, CSS
from hackathon_app.frontend.ui.ui_rendering_typing import render_message, buddy_typing
from hackathon_app.frontend.ui.ui_calendar import select_reminder
from hackathon_app.frontend.ui.ui_rooms import init_rooms, load_room_messages, save_room_messages, create_new_room, switch_room, rename_room, delete_room, reset_current_room

st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS, unsafe_allow_html=True)
# --- CSSの追加 ---
st.markdown("""
<style>
    /* メッセージコンテナを相対位置の基準にする */
    div[data-testid="stChatMessage"] {
        position: relative;
    }

    /* ボタンのスタイルと位置の調整 */
    div[data-testid="stColumn"] button {
        position: absolute;
        bottom: -70px;    /* 下端からの距離（右斜め下へ） */
        right: -45px;     /* 右端からの距離（右斜め下へ） */
        transform: scale(0.5); /* 大きさを半分にする */
        z-index: 1000;    /* 前面に表示 */

        /* --- 背景色を白に変更 --- */
        background-color: #ffffff !important; /* 背景色：白 */
        color: #6c757d !important;           /* アイコンの色：グレー（見やすくするため） */
        
        border-radius: 50% !important;         /* 丸いボタンにする */
        border: 1px solid #dee2e6 !important;    /* 薄いグレーの枠線（白背景と同化しないよう） */
        width: 35px !important;
        height: 35px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1) !important; /* 浮き出し効果（任意） */
    }
    
    /* 3. 編集フォーム全体のデザイン - 白ベースで清潔感を */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0px 8px 24px rgba(0,0,0,0.05) !important;
        margin-top: 15px;
    }

    /* 4. フォーム内のテキストエリア */
    div[data-testid="stForm"] textarea {
        background-color: #f9f9f9 !important;
        border: 1px solid #eeeeee !important;
        border-radius: 8px !important;
    }

    /* 5. フォーム内のボタン（横書き・視認性重視） */
    div[data-testid="stForm"] button {
        position: static !important;
        transform: none !important;
        width: 100% !important;
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px;
        transition: all 0.2s ease !important;
    }

    /* 「修正して送信」ボタン - はっきりした青 */
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        background-color: #1E88E5 !important;
        color: white !important;
        border: none !important;
    }

    /* 「キャンセル」ボタン - 控えめなグレー */
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
        background-color: #f5f5f5 !important;
        color: #757575 !important;
        border: 1px solid #e0e0e0 !important;
    }

    /* ホバー効果 */
    div[data-testid="stForm"] button:hover {
        filter: brightness(0.95);
        box-shadow: 0px 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* 修正中...のインフォメーションを少し控えめに */
    div[data-testid="stForm"] .stAlert {
        background-color: #E3F2FD !important;
        color: #1565C0 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

if "minutes" not in st.session_state:
    st.session_state.minutes = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "show_minutes" not in st.session_state:
    st.session_state.show_minutes = False
if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

rooms = init_rooms()
current_room_id = int(st.session_state.current_room_id)
current_room_name = st.session_state.current_room_name
messages = load_room_messages(current_room_id)
if "messages" not in st.session_state:
    st.session_state.messages = messages

# --- 1. メイン画面: 履歴表示 ---
for idx, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "😎"
    time_str = msg.get("time", "")

    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "user":
            # カラム比率を調整 (0.92:0.08など) してボタンを右端に寄せる
            col_msg, col_btn = st.columns([0.999, 0.001]) 
            
            with col_msg:
                render_message(msg["content"], time_str)

            with col_btn:
                # 既存のボタン
                if st.button("✏️", key=f"edit_btn_{idx}_{len(st.session_state.messages)}", help="編集する"):
                    st.session_state.editing_idx = idx
                    st.rerun()
        else:
            render_message(msg["content"], time_str)

# --- 2. 編集用フォーム (編集ボタンが押された時に割り込んで表示) ---
resubmit_prompt = None
if st.session_state.editing_idx is not None:
    idx = st.session_state.editing_idx
    # 選択されたメッセージがまだ存在するか確認（削除済み対策）
    if idx < len(st.session_state.messages):
        with st.form(key=f"edit_msg_form_{idx}"):
            st.info(f"{idx+1}番目のメッセージを修正中...")
            new_content = st.text_area("修正内容:", value=st.session_state.messages[idx]["content"])
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ 修正して送信"):
                    # 修正箇所「以降」をすべて削除して再送
                    st.session_state.messages = st.session_state.messages[:idx]
                    resubmit_prompt = new_content
                    st.session_state.editing_idx = None
            with col2:
                if st.form_submit_button("❌ キャンセル"):
                    st.session_state.editing_idx = None
                    st.rerun()
    else:
        st.session_state.editing_idx = None

# --- 3. チャット入力 & 送信処理 ---
prompt = st.chat_input("メッセージを入力")

# 通常入力または編集再送信がある場合
final_prompt = prompt if prompt else resubmit_prompt

if final_prompt:
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. ユーザー発言をセッションに追加
    st.session_state.messages.append({"role": "user", "content": final_prompt, "time": current_time})
    save_room_messages(current_room_id, st.session_state.messages)
    
    # 一時的に画面に表示
    with st.chat_message("user", avatar="👤"):
        render_message(final_prompt, current_time)

    # 2. AIの応答を取得
    with st.spinner("通信中..."):
        try:
            payload = {"messages": st.session_state.messages}
            res = requests.post(CHAT_API_URL, json=payload, timeout=30)
            
            if res.status_code == 200:
                response_text = res.json().get("response")
            else:
                error_detail = res.json().get('detail', '不明なエラー')
                response_text = f"サーバーエラー ({res.status_code}): {error_detail}"
            
        except Exception as e:
            response_text = f"エラーが発生しました: {str(e)}"
            
    # 3. AIの返答を保存
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({"role": "assistant", "content": response_text, "time": current_time})
    save_room_messages(current_room_id, st.session_state.messages)
    
    # 完了後にリラン（これで編集フォームも消える）
    st.rerun()

# --- サイドバー ---
with st.sidebar:
    st.write("---")
    st.write("メニュー")
    if st.button("✨ 議事録作成"):
        if messages: 
            st.session_state.show_minutes = False # リセット 

            with st.spinner("整理してるよ..."):
                try:
                    payload = {"messages": messages}
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
