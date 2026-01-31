import os
from hackathon_app.backend.summarize_answer.hf_token_settings import get_hf_client
from hackathon_app.backend.summarize_answer.call_ai_model import call_ai_model

client = get_hf_client()
PROMPT_FILE_PATH = "src/hackathon_app/prompts/minutes_events.txt"


def format_conversation(messages):
    # json形式を [10:30] user: こんにちは のように変換
    formatted_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("time", "時間不明")
        formatted_text += f"[{timestamp}] {role}: {content}\n"
    return formatted_text


def load_prompt_template(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"プロンプトファイルが見つかりません: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_messages(messages: list[dict]) -> str|None:
    if not messages:
        return None
    
    # 全体の開始時刻と終了時刻をあらかじめ抽出
    start_t = messages[0].get("time", "")
    end_t = messages[-1].get("time", "")
    # 会話をテキスト化
    input_text = format_conversation(messages)
    print("【入力テキスト】")
    print(input_text)
    print("-" * 20)

    try:
        print("要約を実行しています...")
    
        prompt_template = load_prompt_template(PROMPT_FILE_PATH)
        prompt = prompt_template.format(
            start_t = start_t,
            end_t = end_t,
            input_text = input_text
        )
        messages_for_api = [
            {"role": "system", "content": "あなたは優秀な議事録AIです"},
            {"role": "user", "content": prompt}
        ]
        
        summary = call_ai_model(
            client,
            messages_for_api,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=500
        )

        return summary
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("別のモデルを試しています...")
        
        # フォールバック: 別のモデルを試す
        try:
            summary = call_ai_model(
                client,
                messages_for_api,
                model="Qwen/Qwen2.5-1.5B-Instruct",
                max_tokens=500
            )
            
            return summary
            
        except Exception as e2:
            print(f"フォールバックも失敗: {e2}")
            return None
