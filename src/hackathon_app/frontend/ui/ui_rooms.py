import streamlit as st
import time
from datetime import datetime
from hackathon_app.frontend.save_load import load_chat, reset_chat

# 初期ルームを作成
def init_rooms():
    if "rooms" not in st.session_state:
        st.session_state.rooms = {
            "トークルーム 1": {"messages": load_chat(), "minutes": "", "events": [], "show_minutes": False}
        }
    if "current_room" not in st.session_state:
        st.session_state.current_room = "トークルーム 1"
    if "delete_confirm_room" not in st.session_state:
        st.session_state.delete_confirm_room = None


def get_current_room():
    return st.session_state.rooms[st.session_state.current_room]


def create_new_room():
    timestamp = datetime.now().strftime("%H%M%S")
    new_name = f"トークルーム {timestamp}"
    st.session_state.rooms[new_name] = {"messages": [], "minutes": "", "events": [], "show_minutes": False}
    st.session_state.current_room = new_name
    st.rerun()


def switch_room(room_name):
    if room_name in st.session_state.rooms:
        st.session_state.current_room = room_name
        st.rerun()


def rename_room(old_name, new_name):
    new_name = new_name.strip()
    rooms = st.session_state.rooms
    rooms[new_name] = rooms.pop(old_name)

    if st.session_state.current_room == old_name:
        st.session_state.current_room = new_name
    

def delete_room(room_name):
    if len(st.session_state.rooms) == 1:
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

    if st.button("✅ 削除する", key=f"yes_{room_name}", use_container_width=True):
        del st.session_state.rooms[room_name]

        if st.session_state.current_room == room_name:
            st.session_state.current_room = list(st.session_state.rooms.keys())[0]

        st.session_state.delete_confirm_room = None
        st.rerun()

    if st.button("❌ キャンセル", key=f"no_{room_name}", use_container_width=True):
        st.session_state.delete_confirm_room = None
        st.rerun()

def reset_current_room():
    room = get_current_room()
    room["messages"] = []
    room["minutes"] = ""
    room["events"] = []
    room["show_minutes"] = False
    st.rerun()
