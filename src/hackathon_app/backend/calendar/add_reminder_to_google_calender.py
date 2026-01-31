from hackathon_app.backend.calendar.setup_google_calendar import get_calendar_service
from datetime import datetime, timedelta

def build_event(e: dict) -> dict:
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
    elif  e["start_time"] and not e["end_time"]:
        start_dt = datetime.fromisoformat(f"{e['date']}T{e['start_time']}")
        end_dt = start_dt + timedelta(hours=1)

        event["start"] = {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Tokyo",
        }
        event["end"] = {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Tokyo",
        }

    else:
        event["start"] = {"date": e["date"]}
        event["end"] = {"date": e["date"]}

    return event


def add_reminder(data: list[dict]) -> None:
    service = get_calendar_service()
    for e in data:
        event = build_event(e)
        created = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()
        # print("予定追加完了: ", created.get("summary"))