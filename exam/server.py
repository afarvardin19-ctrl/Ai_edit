from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            family TEXT,
            nationalCode TEXT,
            phone TEXT,
            email TEXT,
            password TEXT,
            registerDate DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ دیتابیس ساخته شد")

init_db()

@app.route('/')
def index():
    return '''
    <html>
    <body style="text-align:center;padding:40px;font-family:Tahoma;">
        <h1>ثبت نام</h1>
        <form id="f">
            <input type="text" id="name" placeholder="نام"><br><br>
            <input type="text" id="family" placeholder="نام خانوادگی"><br><br>
            <input type="text" id="nationalCode" placeholder="کد ملی"><br><br>
            <input type="text" id="phone" placeholder="شماره تماس"><br><br>
            <input type="email" id="email" placeholder="ایمیل"><br><br>
            <input type="password" id="password" placeholder="رمز"><br><br>
            <button type="submit">ثبت نام</button>
        </form>
        <div id="msg"></div>
        <br>
        <a href="/database">مشاهده دیتابیس</a>
        <script>
            document.getElementById('f').onsubmit = async function(e) {
                e.preventDefault();
                const data = {
                    name: document.getElementById('name').value,
                    family: document.getElementById('family').value,
                    nationalCode: document.getElementById('nationalCode').value,
                    phone: document.getElementById('phone').value,
                    email: document.getElementById('email').value,
                    password: document.getElementById('password').value
                };
                try {
                    const res = await fetch('/register', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    const result = await res.json();
                    document.getElementById('msg').innerHTML = result.message;
                } catch(err) {
                    document.getElementById('msg').innerHTML = '❌ خطا: ' + err;
                }
            };
        </script>
    </body>
    </html>
    '''

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
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
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
def database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY id DESC')
    users = c.fetchall()
    conn.close()
    
    html = '''
    <html>
    <head>
        <style>
            body{font-family:Tahoma;background:#f0f2f5;padding:20px;}
            .box{max-width:1200px;margin:auto;background:white;border-radius:12px;padding:30px;}
            table{width:100%;border-collapse:collapse;margin-top:10px;}
            th{background:#667eea;color:white;padding:12px;border:1px solid #667eea;}
            td{padding:10px;border:1px solid #ddd;text-align:center;}
            tr:nth-child(even){background:#f8f9fa;}
            .count{background:#667eea;color:white;padding:5px 15px;border-radius:20px;display:inline-block;}
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
                <th>تاریخ</th>
            </tr>
    '''
    
    if users:
        for i, u in enumerate(users, 1):
            html += f'<tr><td>{i}</td><td>{u[1]}</td><td>{u[2]}</td><td>{u[3]}</td><td>{u[4]}</td><td>{u[5]}</td><td>{u[6]}</td><td>{u[7]}</td></tr>'
    else:
        html += '<tr><td colspan="8">📭 خالی</td></tr>'
    
    html += '</table></div></body></html>'''
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
