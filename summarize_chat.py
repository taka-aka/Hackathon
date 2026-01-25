from huggingface_hub import InferenceClient
import json
from pathlib import Path

# 1. 準備したトークン
HF_TOKEN = "（自分のキー）"

# InferenceClientを初期化
client = InferenceClient(token=HF_TOKEN)

def format_conversation(messages):
    """
    JSON形式のリスト（role, content, timeを含む）会話履歴リストを単一のテキストに整形する
    """
    formatted_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("time", "時間不明")
        formatted_text += f"[{timestamp}] {role}: {content}\n"
    return formatted_text

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
        
        # プロンプトを作成（日本語で要約を依頼）
        prompt = f"""以下の会話履歴（期間: {start_t} 〜 {end_t}）を、いつ、誰が、どのような流れで話したか明確に要約してください。
特に時間の経過（開始から終了までの流れ）を重視してください。
要約の例：
「21時ちょうど、アイスの話から始まり、その後すぐに伊能先生の結婚や遊園地の話題について短時間で会話した。」

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
                model="Qwen/Qwen2.5-1.5B-Instruct",
                max_tokens=200
            )
            
            summary = result.choices[0].message.content
            return summary
            
        except Exception as e2:
            print(f"フォールバックも失敗: {e2}")
            return None

# --- JSONファイルから読み込むメイン処理 ---
if __name__ == "__main__":
    CHAT_FILE = Path("chat_log.json")
    
    if CHAT_FILE.exists():
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            # JSONファイルを読み込んでリストに変換
            messages_from_json = json.load(f)
        
        # 要約を実行
        summary = summarize_messages(messages_from_json)
        
        if summary:
            print("\n【JSONからの要約結果】")
            print(summary)
    else:
        print(f"エラー: {CHAT_FILE} が見つかりません。")