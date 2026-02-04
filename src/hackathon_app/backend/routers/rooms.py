from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hackathon_app.backend.database import (
    save_messages_by_room_id, get_messages_by_room_id,
    get_rooms, create_room, rename_room_db, delete_room_db,
)

class RenameRoomData(BaseModel):
    old_name: str
    new_name: str

class RoomCreate(BaseModel):
    name: str

router = APIRouter(prefix="/rooms")


@router.get("/get/")
async def load_room():
    try:
        return get_rooms()  # {"1": "トークルーム 1", "2": "トークルーム 2", ...} という辞書で返します。
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        print("ROOMS ERROR:", e)
        raise

@router.post("/create/")
async def make_room(room: RoomCreate):
    try:
        create_room(room.name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename/")
async def rename_room(data: RenameRoomData):
    try:
        rename_room_db(data.old_name, data.new_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{room_id}/delete/")
async def delete_room(room_id: int):
    # ルームを削除する（メッセージも連動して消える）
    delete_room_db(room_id)
    return {"status": "success"}
