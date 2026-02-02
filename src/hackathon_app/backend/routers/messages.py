from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, json, re
from datetime import datetime


class Message(BaseModel):
    role: str
    content: str
    time: str = ""

router = APIRouter(prefix="/messages")

@router.get("/{room_id}/messages")
async def load_messages(room_id: int):
    try:
        return get_messages_by_room_id(room_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{room_id}/messages")
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