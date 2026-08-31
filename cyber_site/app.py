from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import secrets
import string
from pathlib import Path

app = Flask(__name__)
BASE = Path(__file__).parent
DB = BASE / "cyber.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def make_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "VIP-" + "".join(secrets.choice(chars) for _ in range(6))
        con = db()
        exists = con.execute(
            "SELECT 1 FROM users WHERE referral_code=?", (code,)
        ).fetchone()
        con.close()
        if not exists:
            return code

def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            province TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            referral_code TEXT NOT NULL UNIQUE,
            referred_by TEXT,
            points INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("fullName", "").strip()
    age = data.get("age", "").strip()
    province = data.get("province", "").strip()
    city = data.get("city", "").strip()
    phone = data.get("phone", "").strip()
    referral = data.get("referralCode", "").strip().upper()

    if not all([name, age, province, city, phone]):
        return jsonify(ok=False, message="تمام فیلدها الزامی هستند."), 400

    try:
        age = int(age)
    except ValueError:
        return jsonify(ok=False, message="سن نامعتبر است."), 400

    if age < 1 or age > 120:
        return jsonify(ok=False, message="سن نامعتبر است."), 400

    con = db()

    if con.execute("SELECT 1 FROM users WHERE phone=?", (phone,)).fetchone():
        con.close()
        return jsonify(ok=False, message="این شماره قبلاً ثبت شده است."), 409

    inviter = None

    if referral:
        inviter = con.execute(
            "SELECT id, referral_code FROM users WHERE referral_code=?",
            (referral,)
        ).fetchone()

        if not inviter:
            con.close()
            return jsonify(ok=False, message="کد معرف معتبر نیست."), 400

    code = make_code()

    con.execute("""
        INSERT INTO users
        (full_name, age, province, city, phone, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, age, province, city, phone, code, referral or None))

    if inviter:
        con.execute(
            "UPDATE users SET points = points + 5 WHERE id=?",
            (inviter["id"],)
        )

    con.commit()
    con.close()

    return jsonify(
        ok=True,
        message="ثبت‌نام با موفقیت انجام شد.",
        referralCode=code
    )

@app.route("/api/referral/<code>")
def referral_info(code):
    con = db()
    user = con.execute(
        "SELECT referral_code, points FROM users WHERE referral_code=?",
        (code.upper(),)
    ).fetchone()

    if not user:
        con.close()
        return jsonify(ok=False, message="کد معرف پیدا نشد."), 404

    invited = con.execute(
        "SELECT COUNT(*) AS count FROM users WHERE referred_by=?",
        (user["referral_code"],)
    ).fetchone()["count"]

    con.close()

    return jsonify(
        ok=True,
        referralCode=user["referral_code"],
        invited=invited,
        points=user["points"]
    )

init_db()


# شناسه داخلی هر کاربر/جلسه
import uuid
from flask import session

app.secret_key = "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY"

@app.before_request
def assign_user_id():
    if "user_id" not in session:
        session["user_id"] = "USR-" + uuid.uuid4().hex[:12].upper()


from werkzeug.utils import secure_filename

UPLOAD_DIR = BASE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@app.route("/api/location", methods=["POST"])
def save_location():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")

    if user_id is None or latitude is None or longitude is None:
        return jsonify(ok=False, message="اطلاعات موقعیت ناقص است."), 400

    con = db()

    con.execute("""
        INSERT INTO locations
        (user_id, latitude, longitude, accuracy)
        VALUES (?, ?, ?, ?)
    """, (user_id, latitude, longitude, accuracy))

    con.execute("""
        INSERT INTO activity_logs (user_id, action)
        VALUES (?, ?)
    """, (user_id, "location_submitted"))

    con.commit()
    con.close()

    return jsonify(ok=True, message="موقعیت ذخیره شد.")


@app.route("/api/contact", methods=["POST"])
def save_contact():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    name = data.get("contact_name", "").strip()
    phone = data.get("phone", "").strip()

    if user_id is None or not name or not phone:
        return jsonify(ok=False, message="اطلاعات مخاطب ناقص است."), 400

    con = db()

    con.execute("""
        INSERT INTO contacts
        (user_id, contact_name, phone)
        VALUES (?, ?, ?)
    """, (user_id, name, phone))

    con.execute("""
        INSERT INTO activity_logs (user_id, action)
        VALUES (?, ?)
    """, (user_id, "contact_submitted"))

    con.commit()
    con.close()

    return jsonify(ok=True, message="مخاطب ذخیره شد.")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    user_id = request.form.get("user_id")

    if not user_id:
        return jsonify(ok=False, message="شناسه کاربر ارسال نشده است."), 400

    file = request.files.get("file")

    if not file or not file.filename:
        return jsonify(ok=False, message="فایلی انتخاب نشده است."), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify(ok=False, message="نام فایل نامعتبر است."), 400

    saved_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = UPLOAD_DIR / saved_name

    file.save(filepath)

    con = db()

    con.execute("""
        INSERT INTO uploads
        (user_id, filename, filepath)
        VALUES (?, ?, ?)
    """, (user_id, filename, str(filepath)))

    con.execute("""
        INSERT INTO activity_logs (user_id, action)
        VALUES (?, ?)
    """, (user_id, "image_uploaded"))

    con.commit()
    con.close()

    return jsonify(
        ok=True,
        message="فایل ذخیره شد.",
        filename=filename
    )


from functools import wraps
from flask import request

INFO_PASSWORD = "CHANGE-ME-1234"

def info_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.args.get("key") != INFO_PASSWORD:
            return "دسترسی غیرمجاز", 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/information")
@info_auth
def information():
    con = db()

    users = con.execute("""
        SELECT id, full_name, age, province, city, phone,
               referral_code, referred_by, points, created_at
        FROM users ORDER BY id DESC
    """).fetchall()

    locations = con.execute("""
        SELECT id, user_id, latitude, longitude, accuracy, created_at
        FROM locations ORDER BY id DESC
    """).fetchall()

    contacts = con.execute("""
        SELECT id, user_id, contact_name, phone, created_at
        FROM contacts ORDER BY id DESC
    """).fetchall()

    uploads = con.execute("""
        SELECT id, user_id, filename, filepath, uploaded_at
        FROM uploads ORDER BY id DESC
    """).fetchall()

    logs = con.execute("""
        SELECT id, user_id, action, created_at
        FROM activity_logs ORDER BY id DESC
    """).fetchall()

    con.close()

    def table(title, rows):
        if not rows:
            return f"<section><h2>{title}</h2><p>رکوردی وجود ندارد.</p></section>"

        cols = rows[0].keys()
        out = f"<section><h2>{title} <small>({len(rows)})</small></h2><div class='scroll'><table><tr>"
        out += "".join(f"<th>{c}</th>" for c in cols)
        out += "</tr>"

        for row in rows:
            out += "<tr>"
            for c in cols:
                value = row[c]
                out += f"<td>{'' if value is None else value}</td>"
            out += "</tr>"

        out += "</table></div></section>"
        return out

    html = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>اطلاعات | CYBER LAB</title>
<style>
body{margin:0;background:#05080d;color:#e8faff;font-family:Arial;padding:20px}
h1{color:#00e5ff}
h2{color:#00e5ff;margin-top:0}
section{background:#0b111a;border:1px solid #19303d;border-radius:14px;padding:16px;margin:20px 0}
.scroll{overflow:auto}
table{width:100%;border-collapse:collapse;min-width:800px}
th,td{border:1px solid #20303b;padding:8px;white-space:nowrap}
th{background:#111e29;color:#00e5ff}
tr:nth-child(even){background:#091018}
small{color:#8caab5}
</style>
</head>
<body>
<h1>📊 اطلاعات</h1>
<p>اطلاعات ثبت‌شده در پایگاه داده</p>
"""

    html += table("👤 کاربران / ثبت‌نام‌ها", users)
    html += table("📍 موقعیت‌های ارسالی", locations)
    html += table("👥 مخاطبین ارسالی", contacts)
    html += table("🖼 فایل‌ها و عکس‌های ارسالی", uploads)
    html += table("📋 فعالیت‌ها", logs)

    html += "</body></html>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
