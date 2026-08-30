const express = require('express');
const cors = require('cors');
const path = require('path');
const Datastore = require('nedb');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// ===== راه‌اندازی دیتابیس محلی =====
const db = new Datastore({ filename: path.join(__dirname, 'users.db'), autoload: true });

// ===== تولید کد معرف ۵ رقمی =====
function generateReferralCode() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 5; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

// ===== API: دریافت همه کاربران (برای نمایش جدول) =====
app.get('/api/users', (req, res) => {
  db.find({}, (err, users) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(users);
  });
});

// ===== API: ثبت‌نام =====
app.post('/api/signup', (req, res) => {
  const { email, password, referral } = req.body;
  
  db.findOne({ email }, (err, existing) => {
    if (err) return res.status(500).json({ error: err.message });
    if (existing) {
      return res.status(400).json({ error: 'Email already registered' });
    }

    let referralCode = generateReferralCode();
    
    if (referral) {
      db.findOne({ referralCode: referral }, (err, referrer) => {
        if (referrer) {
          db.update({ email: referrer.email }, { $inc: { coins: 15 } }, {}, () => {});
        }
      });
    }

    const user = {
      email,
      password,
      coins: 10,
      referralCode
    };

    db.insert(user, (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({
        success: true,
        message: 'Account created!',
        email,
        coins: user.coins,
        referralCode
      });
    });
  });
});

// ===== API: لاگین =====
app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  
  db.findOne({ email }, (err, user) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!user) {
      return res.status(400).json({ error: 'Account not found' });
    }
    if (user.password !== password) {
      return res.status(400).json({ error: 'Wrong password' });
    }
    
    res.json({
      success: true,
      email: user.email,
      coins: user.coins || 10,
      referralCode: user.referralCode
    });
  });
});

// ===== API: دریافت اطلاعات کاربر =====
app.post('/api/user', (req, res) => {
  const { email } = req.body;
  
  db.findOne({ email }, (err, user) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!user) {
      return res.status(400).json({ error: 'User not found' });
    }
    res.json({
      email: user.email,
      coins: user.coins || 10,
      referralCode: user.referralCode
    });
  });
});

// ===== API: حذف کاربر (فقط برای مدیریت) =====
app.delete('/api/user/:email', (req, res) => {
  const email = req.params.email;
  db.remove({ email }, {}, (err) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, message: 'User deleted' });
  });
});

// ===== راه‌اندازی سرور =====
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📁 Database: ${path.join(__dirname, 'users.db')}`);
});
