import os
from pathlib import Path
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH"))

def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service
 
 
data = [
  {
    "title": "ピクニック",
    "date": "2026-01-29",
    "start_time": "09:00",
    "end_time": ""
  },
  {
    "title": "テスト",
    "date": "2026-01-29",
    "start_time": "",
    "end_time": ""
  }
]

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


def main():
  service = get_calendar_service()
  for e in data:
      event = build_event(e)
      created = service.events().insert(
          calendarId="primary",
          body=event
      ).execute()

      print("end: ", created.get("summary"))


if __name__ == "__main__":
  main()
