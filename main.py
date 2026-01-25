from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
# summarize_chat.pyから要約ロジックをインポート
from summarize_chat import summarize_messages

app = FastAPI()

# リクエストデータの構造を定義
class Message(BaseModel):
    role: str
    content: str
    time: str = "" # UI.pyから送られてくる時間に合わせる

class ChatData(BaseModel):
    messages: List[Message]

@app.post("/generate_minutes")
async def generate_minutes(data: ChatData):
    try:
        # Pydanticモデルを辞書のリストに変換
        messages_dict = [m.model_dump() for m in data.messages]
        
        # summarize_chat.py の関数を実行
        summary = summarize_messages(messages_dict)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="LLMによる要約に失敗しました。")
            
        return {"minutes": summary}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)