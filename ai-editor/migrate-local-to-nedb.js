const Datastore = require('nedb');
const path = require('path');

const db = new Datastore({ filename: path.join(__dirname, 'users.db'), autoload: true });

console.log('📋 برای انتقال اطلاعات، این کد رو توی کنسول مرورگر (F12) بچسبون:');
console.log('');
console.log(`
(async function() {
  const users = JSON.parse(localStorage.getItem('ai_editor_users')) || {};
  const userCoins = JSON.parse(localStorage.getItem('ai_editor_coins')) || {};
  const referralCodes = JSON.parse(localStorage.getItem('ai_editor_referrals')) || {};
  
  const data = { users, userCoins, referralCodes };
  
  const res = await fetch('/api/migrate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const result = await res.json();
  console.log('✅ نتیجه:', result);
})();
`);

// ===== API انتقال =====
const express = require('express');
const app = express();
app.use(express.json());

function generateReferralCode() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 5; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

app.post('/api/migrate', (req, res) => {
  const { users, userCoins, referralCodes } = req.body;
  let count = 0;
  let errors = [];

  for (let email in users) {
    db.findOne({ email }, (err, existing) => {
      if (err) { errors.push(err.message); return; }
      if (!existing) {
        const referralCode = referralCodes[email] || generateReferralCode();
        const user = {
          email: email,
          password: users[email],
          coins: userCoins[email] || 10,
          referralCode: referralCode
        };
        db.insert(user, (err) => {
          if (err) { errors.push(err.message); return; }
          count++;
        });
      }
    });
  }

  setTimeout(() => {
    res.json({ 
      success: true, 
      message: `✅ ${count} کاربر منتقل شدند!`,
      count: count,
      errors: errors.length > 0 ? errors : 'هیچ خطایی نیست'
    });
  }, 1000);
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`🚀 سرور انتقال روی پورت ${PORT} روشن شد`);
  console.log(`📌 کد بالا رو توی کنسول مرورگر (http://localhost:3000) بچسبون`);
});
