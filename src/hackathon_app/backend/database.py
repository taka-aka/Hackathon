import sqlite3
import os

# データベースファイルの保存場所を指定（backendフォルダ直下）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def get_connection():
    """データベースへの接続を取得する"""
    conn = sqlite3.connect(DB_PATH)
    # 取得結果を辞書形式（dict）で扱えるようにする設定
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """データベースとテーブルを初期化する"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                time TEXT NOT NULL
            )
        """)
    print(f"Database initialized at: {DB_PATH}")

def save_message(role: str, content: str, time_str: str):
    """メッセージを保存する"""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO messages (role, content, time) VALUES (?, ?, ?)",
            (role, content, time_str)
        )
        conn.commit()

def get_all_messages():
    """すべてのメッセージを取得する"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT role, content, time FROM messages ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def delete_all_messages():
    """メッセージをすべて削除する（リセット用）"""
    with get_connection() as conn:
        conn.execute("DELETE FROM messages")
        conn.commit()