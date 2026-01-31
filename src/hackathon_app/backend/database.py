import sqlite3
import os

# データベースファイルの保存場所を指定（backendフォルダ直下）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def get_connection():
    """データベースへの接続を取得する"""
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
        cursor = conn.execute("SELECT name FROM rooms")
        return [row["name"] for row in cursor.fetchall()]

def create_room(name):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO rooms (name) VALUES (?)", (name,))
        conn.commit()

def rename_room_db(old_name, new_name):
    with get_connection() as conn:
        conn.execute("UPDATE rooms SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()

def delete_room_db(name):
    with get_connection() as conn:
        # PRAGMA... はSQLiteで外部キー（CASCADE）を有効にするために必要
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
        conn.commit()

# --- メッセージ操作 ---

def save_message(room_name, role, content, time_str):
    with get_connection() as conn:
        # ルーム名からIDを検索して保存
        conn.execute("""
            INSERT INTO messages (room_id, role, content, time)
            SELECT id, ?, ?, ? FROM rooms WHERE name = ?
        """, (role, content, time_str, room_name))
        conn.commit()

def get_messages_by_room(room_name):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT m.role, m.content, m.time 
            FROM messages m
            JOIN rooms r ON m.room_id = r.id
            WHERE r.name = ? ORDER BY m.id ASC
        """, (room_name,))
        return [dict(row) for row in cursor.fetchall()]