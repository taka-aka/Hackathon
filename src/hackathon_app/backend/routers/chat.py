from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

from hackathon_app.backend.summarize_answer.answer_chat import chat_with_llm
from hackathon_app.backend.database import save_message_to_db

class Message(BaseModel):
    role: str
    content: str
    time: str

class ChatData(BaseModel):
    messages: List[Message]

router =APIRouter(prefix="/chat")

@router.post("/{room_name}")
async def chat_endpoint(data: ChatData, room_name: str):
    """チャット応答を生成し、DBに保存する"""
    try:
        user_msg = data.messages[-1]
        save_message_to_db(room_name, user_msg.role, user_msg.content, user_msg.time)

        messages_dict = [m.model_dump() for m in data.messages]
        response = chat_with_llm(messages_dict)

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message_to_db(room_name, "assistant", response, now_time)

        return {"response": response, "time": now_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))