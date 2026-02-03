from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, json, re
from datetime import datetime

from src.hackathon_app.backend.calendar.add_reminder_to_google_calender import add_reminder
from src.hackathon_app.backend.database import (
    init_db, save_message, get_messages_by_room_id, 
    get_rooms, create_room, rename_room_db, delete_room_db
)

class RenameRoomData(BaseModel):
    old_name: str
    new_name: str

router = APIRouter(prefix="/rooms")

@router.post("/create")
async def make_room(name: str):
    try:
        create_room(name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename")
async def rename_room(data: RenameRoomData):
    try:
        rename_room_db(data.old_name, data.new_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{room_id}")
async def delete_room(room_id: int):
    """ルームを削除する（メッセージも連動して消える）"""
    delete_room_db(room_id)
    return {"status": "success"}

@router.get("/get")
async def load_room():
    try:
        return get_rooms()  # {"1": "トークルーム 1", "2": "トークルーム 2", ...} という辞書で返します。
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ルームのチャットをリセット---
@router.delete("/reset/{room_id}")
async def reset_endpoint(room_id: int):
    try:
        delete_all_messages(room_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    