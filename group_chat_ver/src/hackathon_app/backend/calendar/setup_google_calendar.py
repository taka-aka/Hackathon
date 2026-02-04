import os
from pathlib import Path
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 環境変数が取れなかった場合の安全策（ガード）を追加
env_creds = os.getenv("GOOGLE_CREDENTIALS_PATH")
env_token = os.getenv("GOOGLE_TOKEN_PATH")

# 環境変数が取れなかったら "credentials.json" という文字を代わりに使う
CREDENTIALS_PATH = Path(env_creds) if env_creds else Path("credentials.json")
TOKEN_PATH = Path(env_token) if env_token else Path("token.json")

def get_calendar_service():
    creds = None

    # ハードコード（"token.json"など）を、上で定義した変数に置き換え
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

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
 