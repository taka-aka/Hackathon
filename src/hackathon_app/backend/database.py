import sqlite3
import os

# データベースファイルの保存場所を指定（backendフォルダ直下）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def get_connection():
    # データベースへの接続を取得する
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # 取得結果を辞書形式（dict）で扱えるようにする設定

    return conn

def init_db():
    with get_connection() as conn:
        # 1. ルーム管理テーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        # 2. メッセージ管理テーブル（room_idを追加）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE
            )
        """)
        # 初期ルーム「トークルーム 1」がなければ作成
        cursor = conn.execute("SELECT COUNT(*) FROM rooms")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO rooms (name) VALUES ('トークルーム 1')")
        conn.commit()

# --- ルーム操作 ---

def get_rooms():
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, name FROM rooms")
        # {1: "トークルーム 1", 2: "トークルーム 2", ...} という辞書を作成
        return {row["id"]: row["name"] for row in cursor.fetchall()}

def get_messages_by_room_id(room_id: int):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT role, content, time 
            FROM messages 
            WHERE room_id = ? 
            ORDER BY id ASC
        """, (room_id,))
        
        # sqlite3.Row のおかげで dict(row) とするだけで
        # {"role": "...", "content": "...", "time": "..."} の形式になります
        return [dict(row) for row in cursor.fetchall()]

def create_room(name):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO rooms (name) VALUES (?)", (name,))
        conn.commit()

def rename_room_db(old_name, new_name):
    with get_connection() as conn:
        conn.execute("UPDATE rooms SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()

def delete_room_db(id):
    with get_connection() as conn:
        # PRAGMA... はSQLiteで外部キー（CASCADE）を有効にするために必要
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM rooms WHERE id = ?", (id,))
        conn.commit()

# --- メッセージ操作 ---
def delete_room_messages(room_id: int):
    # 指定された room_id に紐づくメッセージ履歴をすべて削除する
    with get_connection() as conn:
        # 指定した room_id のメッセージのみを削除
        conn.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))
        conn.commit()


def save_messages_by_room_id(room_id, messages: list):
    rows = [
        (room_id, msg["role"], msg["content"], msg["time"])  # ここを変更
        for msg in messages
    ]

    with get_connection() as conn:
        cursor = conn.executemany("""
            INSERT INTO messages (room_id, role, content, time)
            VALUES (?, ?, ?, ?)
        """, rows)

        if cursor.rowcount == 0:
            raise ValueError(f"Failed to insert message (room_id={room_id})")
        conn.commit()
