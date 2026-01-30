from hackathon_app.backend.calendar.setup_google_calendar import get_calendar_service

def build_event(e):
    event = {
        "summary": e["title"],
    }

    # 時刻が両方ある → 時間指定イベント, どちらかが空 → 終日イベント
    if e["start_time"] and e["end_time"]:
        event["start"] = {
            "dateTime": f"{e['date']}T{e['start_time']}:00",
            "timeZone": "Asia/Tokyo",
        }
        event["end"] = {
            "dateTime": f"{e['date']}T{e['end_time']}:00",
            "timeZone": "Asia/Tokyo",
        }
    else:
        event["start"] = {"date": e["date"]}
        event["end"] = {"date": e["date"]}

    return event


def add_reminder(data):
    service = get_calendar_service()
    for e in data:
        event = build_event(e)
        created = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()
        # print("予定追加完了: ", created.get("summary"))