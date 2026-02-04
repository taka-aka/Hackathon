from hackathon_app.backend.summarize_answer.hf_token_settings import get_hf_client
from hackathon_app.backend.summarize_answer.call_ai_model import call_ai_model

# アシスタントにLLMを追加
def chat_with_llm(messages):
    client = get_hf_client()
    # プロンプト設定
    api_messages = [
        {"role": "system", "content": "あなたは親しみやすい友達です。タメ口で、短く自然な日本語で返答してください。"}
    ]
    for msg in messages[-10:]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        summary = call_ai_model(
            client,
            api_messages,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=150
        )
        return summary

    except Exception as e:
        print(f"Chat Error: {e}")
        return "ごめん、ちょっとネットの調子悪いかも！"
