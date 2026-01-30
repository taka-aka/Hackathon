import streamlit as st
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
    if not new_name.strip() or old_name not in st.session_state.rooms:
        return
    new_rooms = {}
    for k, v in st.session_state.rooms.items():
        if k == old_name:
            new_rooms[new_name.strip()] = v
    else:
        new_rooms[k] = v                 
    st.session_state.rooms = new_rooms
    

def delete_room(room_name):
    if room_name not in st.session_state.rooms:
        return

    if len(st.session_state.rooms) == 1:
        st.warning("最後のルームは削除できません")
        return
    
    del st.session_state.rooms[room_name]

    # 削除したルームが選択中なら最初のルームに切り替え
    if st.session_state.current_room == room_name:
        st.session_state.current_room = list(st.session_state.rooms.keys())[0]
    st.rerun()


def reset_current_room():
    room = get_current_room()
    room["messages"] = []
    room["minutes"] = ""
    room["events"] = []
    room["show_minutes"] = False
    st.rerun()
