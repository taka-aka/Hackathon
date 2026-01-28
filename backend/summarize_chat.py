from huggingface_hub import InferenceClient
import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN is None:
    raise RuntimeError("環境変数 HF_TOKEN が設定されていません")

# InferenceClientを初期化
client = InferenceClient(token=HF_TOKEN)

BASE_DIR = Path(__file__).parent
# PROMPT_FILE_PATH = BASE_DIR.parent / "prompts" / "summarize.txt"
PROMPT_FILE_PATH = BASE_DIR.parent / "prompts" / "minutes_events.txt"
print("cwd:", Path.cwd())
print("file:", Path(__file__).parent)

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
    # 外部ファイルからプロンプトのテンプレートを読み込む
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"プロンプトファイルが見つかりません: {file_path}")
    
    # encoding='utf-8'を指定して日本語文字化けを防ぐ
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_messages(messages):
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
        
        result = client.chat_completion(
            messages=messages_for_api,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=500
        )
        
        # 結果からテキストを取り出す
        summary = result.choices[0].message.content
        return summary
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("別のモデルを試しています...")
        
        # フォールバック: 別のモデルを試す
        try:
            messages_for_api = [
                {"role": "user", "content": prompt}
            ]
            
            result = client.chat_completion(
                messages=messages_for_api,
                model="Qwen/Qwen2.5-1.5B-Instruct",
                max_tokens=500
            )
            
            summary = result.choices[0].message.content
            return summary
            
        except Exception as e2:
            print(f"フォールバックも失敗: {e2}")
            return None
        
# アシスタントにLLMを追加
def chat_with_llm(messages):
    # プロンプト設定
    api_messages = [
        {"role": "system", "content": "あなたは親しみやすい友達です。タメ口で、短く自然な日本語で返答してください。"}
    ]

    for msg in messages[-10:]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        result = client.chat_completion(
            messages=api_messages,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=150
        )
        return result.choices[0].message.content
    except Exception as e:
        print(f"Chat Error: {e}")
        return "ごめん、ちょっとネットの調子悪いかも！"


# 単体テスト用、chat_log.json から即要約したい
# def main():
#     CHAT_FILE = Path("chat_log.json")
    
#     if not CHAT_FILE.exists():
#         print(f"エラー: {CHAT_FILE} が見つかりません。")
#         return
    
#     with open(CHAT_FILE, "r", encoding="utf-8") as f:
#         messages_from_json = json.load(f)
        
#     # 要約を実行
#     summary = summarize_messages(messages_from_json)
        
#     if summary:
#         print("\n【JSONからの要約結果】")
#         print(summary)


# if __name__ == "__main__":
#     main()
