from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, json, re
# summarize_chat.pyから要約ロジックをインポート
from hackathon_app.backend.summarize.summarize_chat import summarize_messages, chat_with_llm
# --- 既存の /generate_minutes はそのまま ---

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
        # return {"minutes": summary}
        
        # print(summary)
        clean_summary = re.sub(r"```json|```", "", summary).strip()
        try:
            summary_json = json.loads(clean_summary)
        except json.JSONDecodeError:
            summary_json = {
                "minutes": clean_summary,
                "events": []
            }
        return summary_json

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# チャット用の新しいエンドポイント
@app.post("/chat")
async def chat_endpoint(data: ChatData):
    try:
        messages_dict = [m.model_dump() for m in data.messages]
        # チャット応答を生成
        response = chat_with_llm(messages_dict)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)