MINUTES_API_URL = "http://127.0.0.1:8000/generate_minutes"
CHAT_API_URL = "http://127.0.0.1:8000/chat"
CALENDAR_API_URL = "http://127.0.0.1:8000/add_reminder"

PAGE_CONFIG = {
    "page_title": "トーク",
    "page_icon": "💬"
}

CSS = """
    <style>
    .stApp { background-color: #7494C0; }
    div[data-testid="stChatMessage"] { background-color: transparent !important; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) { flex-direction: row-reverse; text-align: right; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) div[data-testid="stMarkdownContainer"] {
        background-color: #8DE055; color: #000; padding: 10px 15px; border-radius: 15px 15px 2px 15px; display: inline-block; margin-right: 10px;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF; color: #000; padding: 10px 15px; border-radius: 15px 15px 15px 2px; display: inline-block; margin-left: 10px;
    }
    </style>
    """