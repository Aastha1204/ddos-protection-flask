import sqlite3
import time, os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'data' / 'logs.db')

def init_db():
    os.makedirs(str(BASE_DIR / 'data'), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT
        )""")

    conn.commit()
    conn.close()

def log_alert(ip, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO alerts (ip, message, timestamp) VALUES (?,?,?)', (ip, message, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_all_logs(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, ip, message, timestamp FROM alerts ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "ip": r[1], "message": r[2], "timestamp": r[3]} for r in rows]

def save_user_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # keep only latest email (simple approach)
    c.execute('DELETE FROM user_email')
    c.execute('INSERT INTO user_email (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()

def get_user_email():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT email FROM user_email ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
