import requests
import sqlite3
import json
import time
import os

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

def sync():
    try:
        print("🔄 دریافت از رندر...")
        response = requests.get(RENDER_URL, timeout=10)
        if response.status_code != 200:
            print(f"❌ خطا: {response.status_code}")
            return
        
        data = response.json()
        users = data.get('users', [])
        
        if not users:
            print("📭 دیتابیس رندر خالی است")
            return
        
        conn = get_db()
        count = 0
        
        for user in users:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO users 
                    (id, name, family, nationalCode, phone, email, password, verify_code, code_time, is_verified, registerDate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.get('id'),
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
        print(f"✅ {count} کاربر منتقل شد!")
        
    except Exception as e:
        print(f"❌ خطا: {e}")

if __name__ == '__main__':
    init_db()
    sync()
    print("✅ همگام‌سازی کامل شد!")
