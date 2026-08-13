import os, secrets
from pathlib import Path
from functools import wraps
from datetime import datetime
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
BASE=Path(__file__).resolve().parent
UPLOADS=BASE/"uploads"; UPLOADS.mkdir(exist_ok=True)
app=Flask(__name__)
app.config["SECRET_KEY"]=os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///"+str(BASE/"club.db")
app.config["MAX_CONTENT_LENGTH"]=10*1024*1024
db=SQLAlchemy(app)

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(30),unique=True,nullable=False)
    first_name=db.Column(db.String(80),nullable=False); last_name=db.Column(db.String(80),nullable=False)
    father_name=db.Column(db.String(80),nullable=False); national_id=db.Column(db.String(20),nullable=False)
    phone=db.Column(db.String(30),nullable=False); address=db.Column(db.Text,nullable=False)
    province=db.Column(db.String(80),nullable=False); county=db.Column(db.String(80),nullable=False)
    age=db.Column(db.Integer,nullable=False); birth_date=db.Column(db.String(30),nullable=False)
    football_experience=db.Column(db.Text); education=db.Column(db.String(120)); school=db.Column(db.String(160))
    father_phone=db.Column(db.String(30)); home_phone=db.Column(db.String(30))
    photo=db.Column(db.String(255)); id_document=db.Column(db.String(255))
    referral_code=db.Column(db.String(30),unique=True,nullable=False); referred_by=db.Column(db.String(30))
    points=db.Column(db.Integer,default=0); created_at=db.Column(db.DateTime,default=datetime.utcnow)

def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not session.get("admin"): return redirect(url_for("login"))
        return f(*a,**kw)
    return w

def save_file(f,prefix):
    if not f or not f.filename:return None
    ext=Path(f.filename).suffix.lower()
    allowed={".jpg",".jpeg",".png",".webp",".pdf"}
    if ext not in allowed: raise ValueError("فرمت فایل مجاز نیست.")
    name=f"{prefix}_{secrets.token_hex(12)}{ext}"
    f.save(UPLOADS/name); return name

def telegram_send(student):
    token=os.getenv("TELEGRAM_BOT_TOKEN","")
    chat=os.getenv("TELEGRAM_CHAT_ID","")
    if not token or not chat or token.startswith("PUT_"): return False
    base=f"https://api.telegram.org/bot{token}"
    text=(f"📋 ثبت‌نام جدید | باشگاه فوتبال زنجان\n\n"
          f"🆔 {student.code}\n👤 {student.first_name} {student.last_name}\n"
          f"👨 نام پدر: {student.father_name}\n🪪 کد ملی: {student.national_id}\n"
          f"📱 تماس: {student.phone}\n📞 پدر: {student.father_phone or '-'}\n☎️ منزل: {student.home_phone or '-'}\n"
          f"📍 {student.province} / {student.county}\n🏠 {student.address}\n"
          f"🎂 سن: {student.age}\n📅 تولد: {student.birth_date}\n"
          f"⚽ تجربه: {student.football_experience or '-'}\n🎓 رشته: {student.education or '-'}\n🏫 مدرسه: {student.school or '-'}\n"
          f"⭐ امتیاز: {student.points}\n🔗 کد معرف: {student.referral_code}\n")
    try:
        r=requests.post(base+"/sendMessage",json={"chat_id":chat,"text":text},timeout=15)
        if not r.ok:return False
        for field,caption in [(student.photo,"📷 عکس شاگرد"),(student.id_document,"🪪 کپی شناسنامه")]:
            if field:
                path=UPLOADS/field
                endpoint="/sendPhoto" if Path(field).suffix.lower() in {".jpg",".jpeg",".png",".webp"} else "/sendDocument"
                key="photo" if endpoint=="/sendPhoto" else "document"
                with open(path,"rb") as fp:
                    rr=requests.post(base+endpoint,data={"chat_id":chat,"caption":caption},files={key:fp},timeout=30)
                    if not rr.ok:return False
        return True
    except requests.RequestException:return False

@app.route("/",methods=["GET","POST"])
def register():
    if request.method=="POST":
        try:
            s=Student(code="ZN-"+secrets.token_hex(4).upper(),
                      first_name=request.form["first_name"].strip(),last_name=request.form["last_name"].strip(),
                      father_name=request.form["father_name"].strip(),national_id=request.form["national_id"].strip(),
                      phone=request.form["phone"].strip(),address=request.form["address"].strip(),
                      province=request.form["province"].strip(),county=request.form["county"].strip(),
                      age=int(request.form["age"]),birth_date=request.form["birth_date"].strip(),
                      football_experience=request.form.get("football_experience","").strip(),
                      education=request.form.get("education","").strip(),school=request.form.get("school","").strip(),
                      father_phone=request.form.get("father_phone","").strip(),home_phone=request.form.get("home_phone","").strip(),
                      referral_code="REF-"+secrets.token_hex(4).upper(),referred_by=request.form.get("referral","").strip() or None)
            s.photo=save_file(request.files.get("photo"),"photo")
            s.id_document=save_file(request.files.get("id_document"),"id")
            db.session.add(s); db.session.commit()
            sent=telegram_send(s)
            return render_template("success.html",student=s)
        except Exception as e:
            db.session.rollback(); flash(str(e))
    return render_template("register.html",referral=request.args.get("ref",""))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("username")==os.getenv("ADMIN_USERNAME","admin") and request.form.get("password")==os.getenv("ADMIN_PASSWORD","CHANGE_THIS_PASSWORD"):
            session["admin"]=True; return redirect(url_for("dashboard"))
        flash("نام کاربری یا رمز عبور نادرست است.")
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/admin")
@admin_required
def dashboard():
    q=request.args.get("q","").strip()
    query=Student.query
    if q: query=query.filter((Student.first_name.contains(q))|(Student.last_name.contains(q))|(Student.code.contains(q))|(Student.national_id.contains(q)))
    students=query.order_by(Student.created_at.desc()).all()
    return render_template("dashboard.html",students=students,q=q)

@app.route("/admin/student/<int:id>/edit",methods=["GET","POST"])
@admin_required
def edit(id):
    s=Student.query.get_or_404(id)
    if request.method=="POST":
        for f in ["first_name","last_name","father_name","national_id","phone","address","province","county","birth_date","football_experience","education","school","father_phone","home_phone"]:
            setattr(s,f,request.form.get(f,"").strip())
        s.age=int(request.form.get("age",s.age)); s.points=int(request.form.get("points",s.points))
        db.session.commit(); flash("ذخیره شد."); return redirect(url_for("dashboard"))
    return render_template("edit.html",s=s)

@app.route("/admin/student/<int:id>/delete",methods=["POST"])
@admin_required
def delete(id):
    s=Student.query.get_or_404(id); db.session.delete(s); db.session.commit()
    return redirect(url_for("dashboard"))

with app.app_context(): db.create_all()
if __name__=="__main__": app.run(debug=True)
