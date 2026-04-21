import sqlite3
import json

DB_FILE = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ChatHistory (
            UserName TEXT,
            BookName TEXT,
            Messages TEXT,
            Created_DT DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (UserName, BookName)
        )
    ''')
    conn.commit()
    conn.close()

def save_history(user, book, messages):
    conn = sqlite3.connect(DB_FILE)
    msg_json = json.dumps(messages)
    conn.execute('''
        INSERT OR REPLACE INTO ChatHistory (UserName, BookName, Messages, Created_DT)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user, book, msg_json))
    conn.commit()
    conn.close()

def load_history(user, book):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT Messages FROM ChatHistory WHERE UserName=? AND BookName=?", (user, book))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []