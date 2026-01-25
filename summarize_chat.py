from huggingface_hub import InferenceClient

# 1. 準備したトークン
HF_TOKEN = ""

# InferenceClientを初期化
client = InferenceClient(token=HF_TOKEN)

# プロンプトファイルのパス（スクリプトと同じ階層にある場合）
PROMPT_FILE_PATH = "prompt/summarize.txt"

def format_conversation(messages):
    """
    会話履歴リストを単一のテキストに整形する
    """
    formatted_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted_text += f"{role}: {content}\n"
    return formatted_text

def load_prompt_template(file_path):
    """
    外部ファイルからプロンプトのテンプレートを読み込む
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"プロンプトファイルが見つかりません: {file_path}")
    
    # encoding='utf-8'を指定して日本語文字化けを防ぐ
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def summarize_messages(messages):
    # 会話をテキスト化
    input_text = format_conversation(messages)
    print("【入力テキスト】")
    print(input_text)
    print("-" * 20)

    try:
        print("要約を実行しています...")
        
        # プロンプトを作成（日本語で要約を依頼）
        prompt = f"""以下の会話を1〜2文で簡潔に要約してください。

会話:
{input_text}

要約:"""
        
        # chat_completionを使用（日本語対応のLLM）
        messages_for_api = [
            {"role": "user", "content": prompt}
        ]
        
        result = client.chat_completion(
            messages=messages_for_api,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=200
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
                model="microsoft/Phi-3-mini-4k-instruct",
                max_tokens=200
            )
            
            summary = result.choices[0].message.content
            return summary
            
        except Exception as e2:
            print(f"フォールバックも失敗: {e2}")
            return None

# テストデータ
input_data = {
 "messages": [
     {"role": "user", "content": "こんにちは"},
     {"role": "assistant", "content": "お疲れ！"},
     {"role": "user", "content": "明日の会議の時間は何時でしたっけ？"},
     {"role": "assistant", "content": "明日は14時から会議室Aで行います。資料の準備をお願いしますね。"},
     {"role": "user", "content": "了解しました。資料はすでに作成済みです。"},
     {"role": "assistant", "content": "素晴らしい！では明日よろしくお願いします。"}
   ]
 }

if __name__ == "__main__":
    messages = input_data["messages"]
    summary = summarize_messages(messages)
    
    if summary:
        print("\n【要約結果】")
        print(summary)
