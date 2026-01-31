from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, json, re
from datetime import datetime

from src.hackathon_app.backend.summarize.summarize_chat import summarize_messages, chat_with_llm
from src.hackathon_app.backend.calendar.add_reminder_to_google_calender import add_reminder
from src.hackathon_app.backend.database import (
    init_db, save_message, get_messages_by_room_id, 
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

@app.get("/rooms/get")
async def load_room():
    try:
        return get_rooms()  # {"1": "トークルーム 1", "2": "トークルーム 2", ...} という辞書で返します。
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms/{room_id}/messages")
async def load_messages(room_id: int):
    try:
        return get_messages_by_room_id(room_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rooms/create")
async def make_room(name: str):
    try:
        create_room(name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rooms/rename")
async def rename_room(data: RenameRoomData):
    try:
        rename_room_db(data.old_name, data.new_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rooms/{room_id}")
async def delete_room(room_id: int):
    """ルームを削除する（メッセージも連動して消える）"""
    delete_room_db(room_id)
    return {"status": "success"}

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

@app.post("/rooms/{room_id}/messages")
async def save_message_endpoint(room_id: int, data: Message):
    """
    フロントエンドからメッセージを受け取り、指定されたルーム名に保存する
    """
    try:
        # database.py の関数を呼び出し
        database.save_message_to_db(
            room_name=room_name,
            role=data.role,
            content=data.content,
            time_str=data.time
        )
        return {"status": "success", "message": "Message saved successfully"}
    except Exception as e:
        # データベースエラーなどが発生した場合
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

# --- ルームのチャットをリセット---
@app.delete("/room/{room_id}/reset")
async def reset_endpoint(room_id: int):
    try:
        delete_all_messages(room_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    