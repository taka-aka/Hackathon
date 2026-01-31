from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, json, re
from datetime import datetime

from src.hackathon_app.backend.summarize.summarize_chat import summarize_messages, chat_with_llm
from src.hackathon_app.backend.calendar.add_reminder_to_google_calender import add_reminder
from src.hackathon_app.backend.database import (
    init_db, save_message, get_messages_by_room, 
    get_rooms, create_room, rename_room_db, delete_room_db
)
app = FastAPI()

# データベースの初期化
@app.on_event("startup")
def on_startup():
    init_db()


def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
         raise ValueError("JSONが見つかりません")
    
    json_str = text[start:end]
    print(json_str)
    try:
        summary_json = json.loads(json_str)
    except json.JSONDecodeError:
            summary_json = {
                "minutes": json_str,
                "events": []
            }
    return summary_json

class Message(BaseModel):
    role: str
    content: str
    time: str = ""

class ChatData(BaseModel):
    messages: List[Message]

class RenameRoomData(BaseModel):
    old_name: str
    new_name: str

@app.get("/rooms")
async def fetch_rooms():
    """ルーム名の一覧を返す"""
    return {"rooms": get_rooms()}

@app.post("/rooms/create")
async def make_room(name: str):
    """新しいルームを作成する"""
    create_room(name)
    return {"status": "success"}

@app.post("/rooms/rename")
async def rename_room(data: RenameRoomData):
    """ルーム名を変更する"""
    rename_room_db(data.old_name, data.new_name)
    return {"status": "success"}

@app.delete("/rooms/{name}")
async def delete_room(name: str):
    """ルームを削除する（メッセージも連動して消える）"""
    delete_room_db(name)
    return {"status": "success"}

# --- 履歴取得用のエンドポイント ---
@app.get("/history/{room_name}")
async def history_endpoint():
    try:
        messages = get_messages_by_room(room_name)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(data: ChatData, room_name: str):
    """チャット応答を生成し、DBに保存する"""
    try:
        user_msg = data.messages[-1]
        save_message(room_name, user_msg.role, user_msg.content, user_msg.time)

        messages_dict = [m.model_dump() for m in data.messages]
        response = chat_with_llm(messages_dict)

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message(room_name, "assistant", response, now_time)

        return {"response": response, "time": now_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_minutes")
async def generate_minutes(data: ChatData):
    try:
        # Pydanticモデルを辞書のリストに変換
        messages_dict = [m.model_dump() for m in data.messages]
        
        # summarize_chat.py の関数を実行
        summary = summarize_messages(messages_dict)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="LLMによる要約に失敗しました。")  
        # return {"minutes": summary}
    
        print(summary)
        summary_json = extract_json(summary)
        return summary_json

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add_reminder")
def handle_calendar(data: dict):
    events = data.get("events")
    result = add_reminder(events)
    return {"status": "success"}



# --- リセット用のエンドポイント ---
@app.post("/reset")
async def reset_endpoint():
    try:
        delete_all_messages()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    