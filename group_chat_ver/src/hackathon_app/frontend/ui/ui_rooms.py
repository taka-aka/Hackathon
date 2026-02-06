import streamlit as st
import requests
from datetime import datetime
from hackathon_app.frontend.ui.ui_settings import ROOMS_API_URL, ROOM_API_URL


# 初期ルームを作成
def get_rooms():
    try:
        res = requests.get(ROOMS_API_URL+"/get/")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error("部屋が取得できなかった")
        return {}


from hackathon_app.backend.database import init_db, get_rooms as db_get_rooms
import streamlit as st

def init_rooms():
    # DB初期化（テーブルと初期ルーム）
    init_db()

    # DBからルーム取得
    rooms = db_get_rooms()

    # DBにルームがなければ最低限のデフォルト
    if not rooms:
        rooms = {0: "初期ルーム"}

    # session_state 初期化
    if "current_room_id" not in st.session_state:
        st.session_state.current_room_id = list(rooms.keys())[0]
    if "current_room_name" not in st.session_state:
        st.session_state.current_room_name = list(rooms.values())[0]
    if "delete_confirm_room" not in st.session_state:
        st.session_state.delete_confirm_room = None

    return rooms



def load_room_messages(room_id):
    try:
        res = requests.get(f"{ROOM_API_URL}/{room_id}/load_messages/")
        res.raise_for_status()
        return res.json()
    except:
        st.error("部屋の会話履歴が取得できなかった")
        return []


def save_room_messages(room_id, messages):
    try:
        res = requests.post(
            f"{ROOM_API_URL}/{room_id}/save_messages/", 
            json={"messages": messages}
        )
        res.raise_for_status()
    except:
        st.error("部屋の会話履歴が保存できなかった")


def create_new_room():
    timestamp = datetime.now().strftime("%H%M%S")
    try:
        res = requests.post(
            ROOMS_API_URL+"/create/",
            json={"name": f"トークルーム{timestamp}"}
        )
        res.raise_for_status()
    except:
        st.error("部屋を作成できなかった")
        return

    rooms = get_rooms()
    new_room_id = list(rooms.keys())[-1]
    st.session_state.current_room_id = int(new_room_id)
    st.session_state.current_room_name = rooms[new_room_id]
    st.rerun()


def switch_room(room_name, room_id):
    st.session_state.current_room_id = int(room_id)
    st.session_state.current_room_name = room_name
    st.session_state.messages = load_room_messages(room_id)
    st.rerun()


def rename_room(old_name, new_name):
    try:
        requests.post(
            ROOMS_API_URL+"/rename/", 
            json={"old_name": old_name, "new_name": new_name}
        )
    except:
        st.error("部屋名を変更できなかった")

    if st.session_state.current_room_name == old_name:
        st.session_state.current_room_name = new_name
    st.rerun()


def delete_room(room_name, room_id):
    rooms = get_rooms()
    if len(rooms) == 1:
        if st.button("🗑️ 削除", key=f"del_{room_name}", use_container_width=True):
            st.warning("最後のルームは削除できません")
        return

    # まだ確認段階じゃない
    if st.session_state.delete_confirm_room != room_name:
        if st.button("🗑️ 削除", key=f"del_{room_name}", use_container_width=True):
            st.session_state.delete_confirm_room = room_name
            st.rerun()
        return

    # 確認段階
    st.error(f"本当に「{room_name}」を削除しますか？")
    if st.button("❌ キャンセル", key=f"no_{room_name}", use_container_width=True):
        st.session_state.delete_confirm_room = None
        st.rerun()
    if st.button("✅ 削除する", key=f"yes_{room_name}", use_container_width=True):
        try:
            requests.delete(f"{ROOMS_API_URL}/{room_id}/delete")
        except:
            st.error("部屋を削除できなかった")

        st.session_state.delete_confirm_room = None
        if st.session_state.current_room_id == room_id:
            rooms = get_rooms()
            st.session_state.current_room_id = list(rooms.keys())[0]
            st.session_state.current_room_name = list(rooms.values())[0]
    st.rerun()


def reset_current_room(room_id):
    try:
        res = requests.delete(f"{ROOM_API_URL}/{room_id}/reset/")
        if res.status_code != 200:
            st.error(f"失敗: {res.status_code}\n{res.text}")
    except:
        st.error("部屋の会話履歴をリセットできなかった")
    st.session_state.messages = []  
    st.rerun()
