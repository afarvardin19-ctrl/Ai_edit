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

@app.route('/export')
def export():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    conn.close()
    # حذف verify_code از خروجی
    result = []
    for user in users:
        user_dict = dict(user)
        user_dict.pop('verify_code', None)  # حذف کد تایید
        result.append(user_dict)
    return jsonify({'users': result})

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
def view_database():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>دیتابیس</title>
    <style>
        body{font-family:Tahoma;background:#f0f2f5;padding:20px;}
        .box{max-width:1200px;margin:auto;background:white;border-radius:12px;padding:30px;}
        table{width:100%;border-collapse:collapse;margin-top:10px;}
        th{background:#667eea;color:white;padding:12px;border:1px solid #667eea;}
        td{padding:10px;border:1px solid #ddd;text-align:center;}
        tr:nth-child(even){background:#f8f9fa;}
        .count{background:#667eea;color:white;padding:5px 15px;border-radius:20px;display:inline-block;}
        .verified{color:green;font-weight:bold;}
        .not-verified{color:orange;font-weight:bold;}
    </style>
    </head>
    <body>
    <div class="box">
        <h1>📊 دیتابیس</h1>
        <a href="/">← بازگشت</a><br><br>
        <span class="count">تعداد: ''' + str(len(users)) + ''' نفر</span><br><br>
        <table>
            <tr>
                <th>ردیف</th>
                <th>نام</th>
                <th>نام خانوادگی</th>
                <th>کد ملی</th>
                <th>شماره</th>
                <th>ایمیل</th>
                <th>رمز</th>
                <th>وضعیت</th>
            </tr>
    '''
    
    if users:
        for i, u in enumerate(users, 1):
            status = '✅ تایید' if u['is_verified'] == 1 else '⏳ در انتظار'
            cls = 'verified' if u['is_verified'] == 1 else 'not-verified'
            html += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{u['name']}</td>
                        <td>{u['family']}</td>
                        <td>{u['nationalCode']}</td>
                        <td>{u['phone']}</td>
                        <td>{u['email']}</td>
                        <td>{u['password']}</td>
                        <td class="{cls}">{status}</td>
                    </tr>
            '''
    else:
        html += '<tr><td colspan="8">📭 دیتابیس خالی است</td></tr>'
    
    html += '</table></div></body></html>'''
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
