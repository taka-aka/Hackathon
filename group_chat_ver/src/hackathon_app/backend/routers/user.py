from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from hackathon_app.backend.database import (
    get_users_db, create_new_user_db
)

class UserCreate(BaseModel):
    username: str
    avatar: str

router = APIRouter(prefix="/user")


@router.get("/get/")
async def get_users():
    try:
        return get_users_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create/")
async def create_new_user(data: UserCreate):
    try:
        user = create_new_user_db(data.username, data.avatar)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
