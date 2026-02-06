import streamlit  as st
import requests
from hackathon_app.frontend.ui.ui_settings import USER_API_URL

def get_user():
    try:
        res = requests.get(f"{USER_API_URL}/get/")
        res.raise_for_status()
        return res.json()
    except:
        st.error("ユーザー情報が取得できなかった")
        return []


def create_user(username, avatar):
    try:
        res = requests.post(
            f"{USER_API_URL}/create/",
            json={"username": username, "avatar": avatar}
        )
        res.raise_for_status()
        return res.json()
    except:
        st.error("ユーザー作成ができなかった")

def init_username():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.avatar = None

    users = get_user()
    user_map = {u["username"]: u for u in users}

    with st.expander("👤 ユーザー選択 / 新規作成"):
        options = ["新規登録"] + [u["username"] for u in users]
        selected = st.selectbox("ユーザー選択", options)

        if selected == "新規登録":
            new_name = st.text_input("新しいユーザー名")
            avatar = st.selectbox(
                "アイコンを選んでね",
                ["😀", "😎", "🐱", "🐶", "🦊", "🐼"]
            )

            if st.button("この名前で入室"):
                if not new_name.strip():
                    st.warning("名前を入力してね")
                elif new_name.strip() in user_map.keys():
                    st.error("⚠️ その名前はすでに使われています")
                else:
                    user = create_user(new_name.strip(), avatar)
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]
                    st.session_state.avatar = user["avatar"]
                    st.rerun()

        else:
            user = user_map[selected]
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.session_state.avatar = user["avatar"]

    if st.session_state.user_id is None:
        st.info("👆 まずユーザーを選択または作成してください")
        st.stop()
