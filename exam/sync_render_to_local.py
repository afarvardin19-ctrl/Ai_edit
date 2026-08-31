import requests
import sqlite3
import json

RENDER_URL = "https://exam-site-y5ah.onrender.com/export"
LOCAL_DB = "database.db"

def get_db():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            family TEXT,
            nationalCode TEXT UNIQUE,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT,
            verify_code TEXT,
            code_time INTEGER,
            is_verified INTEGER DEFAULT 0,
            registerDate DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ دیتابیس محلی آماده شد")

def fetch_from_render():
    try:
        response = requests.get(RENDER_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('users', [])
        else:
            print(f"❌ خطا در دریافت: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ خطا: {e}")
        return []

def save_to_local(users):
    if not users:
        print("📭 هیچ کاربری در رندر نیست")
        return
    
    conn = get_db()
    count = 0
    for user in users:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO users 
                (name, family, nationalCode, phone, email, password, verify_code, code_time, is_verified, registerDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.get('name', ''),
                user.get('family', ''),
                user.get('nationalCode', ''),
                user.get('phone', ''),
                user.get('email', ''),
                user.get('password', ''),
                user.get('verify_code', ''),
                user.get('code_time', 0),
                user.get('is_verified', 0),
                user.get('registerDate', '')
            ))
            conn.commit()
            count += 1
        except Exception as e:
            print(f"❌ خطا در ذخیره {user.get('name')}: {e}")
    conn.close()
    print(f"✅ {count} کاربر به دیتابیس محلی اضافه شد")

if __name__ == '__main__':
    print("🔄 در حال دریافت از رندر...")
    init_db()
    users = fetch_from_render()
    save_to_local(users)
