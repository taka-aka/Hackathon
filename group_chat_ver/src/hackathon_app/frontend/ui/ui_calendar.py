import streamlit as st
import requests
from hackathon_app.frontend.ui.ui_settings import CALENDAR_API_URL

def select_reminder(events):
    if not events:
        return
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
            payload = {"events": selected_events}
            res = requests.post(CALENDAR_API_URL, json=payload)
            if res.status_code == 200:
                st.success("Googleカレンダーに追加したよ！🎉")  
