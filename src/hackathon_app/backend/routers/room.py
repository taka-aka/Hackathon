# 各ルーム別の操作
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from src.hackathon_app.backend.database import (
    delete_room_messages, get_messages_by_room_id, save_messages_by_room_id
)

class Message(BaseModel):
    role: str
    content: str
    time: str

class ChatData(BaseModel):
    messages: List[Message]

router = APIRouter(prefix="/room")


@router.delete("/{room_id}/reset/")
async def reset_endpoint(room_id: int):
    try:
        delete_room_messages(room_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{room_id}/load_messages/")
async def load_messages(room_id: int):
    try:
        return get_messages_by_room_id(room_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{room_id}/save_messages/")
async def save_message_endpoint(room_id: int, data: ChatData):
    delete_room_messages(room_id)

    try:
        messages_dicts = [m.model_dump() for m in data.messages]
        print("DEBUG messages_dicts:", messages_dicts)
        save_messages_by_room_id(room_id, messages_dicts)
        return {"status": "success", "message": "Message saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
