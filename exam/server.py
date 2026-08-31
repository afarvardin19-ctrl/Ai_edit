from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import random
import time
import os

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('database.db')
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
    print("✅ دیتابیس آماده شد")

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/db')
def database_page():
    return send_from_directory('.', 'db.html')

@app.route('/export')
def export():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({'users': [dict(user) for user in users]})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip()
    family = data.get('family', '').strip()
    nationalCode = data.get('nationalCode', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not all([name, family, nationalCode, phone, email, password]):
        return jsonify({'message': '❌ همه فیلدها الزامی است'})
    
    verify_code = str(random.randint(100000, 999999))
    
    try:
        conn = get_db()
        conn.execute('''
            INSERT INTO users (name, family, nationalCode, phone, email, password, verify_code, code_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, family, nationalCode, phone, email, password, verify_code, int(time.time())))
        conn.commit()
        conn.close()
        return jsonify({'message': '✅ ثبت نام موفق! کد: ' + verify_code})
    except sqlite3.IntegrityError:
        return jsonify({'message': '❌ کد ملی یا ایمیل تکراری است'})
    except Exception as e:
        return jsonify({'message': '❌ خطا: ' + str(e)})

@app.route('/database')
def database():
    return send_from_directory('.', 'db.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
