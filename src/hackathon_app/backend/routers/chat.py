from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from hackathon_app.backend.summarize_answer.answer_chat import chat_with_llm

class Message(BaseModel):
    role: str
    content: str
    time: str

class ChatData(BaseModel):
    messages: List[Message]

router =APIRouter(prefix="/chat")


@router.post("/")
async def chat_endpoint(data: ChatData):
    try:
        messages_dict = [m.model_dump() for m in data.messages]
        # チャット応答を生成
        response = chat_with_llm(messages_dict)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
