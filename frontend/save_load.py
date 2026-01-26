import json, os
from pathlib import Path

CHAT_FILE = Path("chat_log.json")

def save_chat(messages):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
        # ensure_ascii=False で文字をそのまま保存、indent=2で2階層識別

def load_chat():
    if not CHAT_FILE.exists():
        return []
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        print('ロード完了')
        return json.load(f)

def reset_chat():
    if not CHAT_FILE.exists():
        return
    os.remove(CHAT_FILE)