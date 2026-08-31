from flask import Flask, request, jsonify, send_from_directory
import sqlite3
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
            registerDate DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ دیتابیس با رمز ساخته شد")

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

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
    
    try:
        conn = get_db()
        conn.execute('''
            INSERT INTO users (name, family, nationalCode, phone, email, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, family, nationalCode, phone, email, password))
        conn.commit()
        conn.close()
        return jsonify({'message': '✅ ثبت نام موفق!'})
    except sqlite3.IntegrityError:
        return jsonify({'message': '❌ کد ملی یا ایمیل تکراری است'})
    except Exception as e:
        return jsonify({'message': '❌ خطا: ' + str(e)})

@app.route('/database')
def view_database():
    conn = get_db()
    users = conn.execute('SELECT id, name, family, nationalCode, phone, email, password, registerDate FROM users ORDER BY id DESC').fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>دیتابیس</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box;}
            body{font-family:Tahoma;background:#f0f2f5;padding:20px;}
            .box{max-width:1200px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.1);}
            h1{color:#333;border-bottom:3px solid #667eea;padding-bottom:10px;margin-bottom:20px;text-align:center;}
            .back-btn{display:inline-block;background:#667eea;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;margin-bottom:20px;}
            .back-btn:hover{background:#764ba2;}
            .count{background:#667eea;color:white;padding:5px 15px;border-radius:20px;display:inline-block;margin-bottom:15px;}
            .table-wrap{overflow-x:auto;}
            table{width:100%;border-collapse:collapse;margin-top:10px;}
            th{background:#667eea;color:white;padding:12px;border:1px solid #667eea;}
            td{padding:10px;border:1px solid #ddd;text-align:center;}
            tr:nth-child(even){background:#f8f9fa;}
            tr:hover{background:#e8f0fe;}
            .empty{text-align:center;color:#999;padding:20px;}
        </style>
    </head>
    <body>
    <div class="box">
        <h1>📊 دیتابیس کاربران</h1>
        <a href="/" class="back-btn">← بازگشت به صفحه اصلی</a><br><br>
        <span class="count">تعداد کاربران: ''' + str(len(users)) + ''' نفر</span><br><br>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>ردیف</th>
                        <th>نام</th>
                        <th>نام خانوادگی</th>
                        <th>کد ملی</th>
                        <th>شماره تماس</th>
                        <th>ایمیل</th>
                        <th>رمز عبور</th>
                        <th>تاریخ ثبت</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    if users:
        for i, u in enumerate(users, 1):
            html += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{u['name']}</td>
                        <td>{u['family']}</td>
                        <td>{u['nationalCode']}</td>
                        <td>{u['phone']}</td>
                        <td>{u['email']}</td>
                        <td>{u['password']}</td>
                        <td>{u['registerDate']}</td>
                    </tr>
            '''
    else:
        html += '<tr><td colspan="8" class="empty">📭 دیتابیس خالی است</td></tr>'
    
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
