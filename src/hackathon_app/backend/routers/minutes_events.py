from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json
from hackathon_app.backend.summarize_answer.summarize_chat import summarize_messages

def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
         raise ValueError("JOSNが見つかりません")
    
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

# リクエストデータの構造を定義
class Message(BaseModel):
    role: str
    content: str
    time: str = "" # UI.pyから送られてくる時間に合わせる

class ChatData(BaseModel):
    messages: List[Message]

router = APIRouter(prefix="/generate_minutes")

@router.post("/")
async def generate_minutes(data: ChatData):
    try:
        # Pydanticモデルを辞書のリストに変換
        messages_dict = [m.model_dump() for m in data.messages]
        
        # summarize_chat.py の関数を実行
        summary = summarize_messages(messages_dict)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="LLMによる要約に失敗しました。")  
    
        summary_json = extract_json(summary)
        return summary_json

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
