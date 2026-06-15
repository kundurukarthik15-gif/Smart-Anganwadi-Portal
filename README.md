# Smart Anganwadi Portal — Backend API

Complete production-ready Flask backend for the Smart Anganwadi Portal.

---

## Files

```
app.py            ← Complete Flask backend (single file)
.env              ← Environment variables
requirements.txt  ← Python dependencies
sql/              ← Folder containing all Supabase database schema & seed scripts
README.md         ← This file
```

---

## Database Tables (10 Tables)

| # | Table | Description |
|---|-------|-------------|
| 1 | `centers` | Anganwadi center details (name, district, mandal, village) |
| 2 | `users` | Staff members linked to a center (email + hashed password) |
| 3 | `children` | Child records with age, gender, parent info |
| 4 | `beneficiaries` | Pregnant women and lactating mothers |
| 5 | `stock_entries` | Nutrition stock inventory per center |
| 6 | `stock_distribution` | Distribution history log |
| 7 | `stock_logs` | Audit trail for all stock actions |
| 8 | `stories` | Digital story library (PDF + audio) |
| 9 | `meetings` | Meeting schedule and history |
| 10 | `surveys_feedback` | Parent feedback with ratings |

---

## Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → Create new project
2. Go to **SQL Editor** → **New Query**
3. Paste the entire contents of `schema.sql` → Click **Run**
4. Go to **Settings** → **API** → Copy:
   - `Project URL` → paste as `SUPABASE_URL` in `.env`
   - `anon public` key → paste as `SUPABASE_KEY` in `.env`

---

## Step 2 — Local Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Fill in .env with your Supabase credentials

# Run development server
python app.py
```

API will be running at: `http://localhost:5000`

---

## Step 3 — Connect Frontend

Update `script.js` in the frontend — replace demo login with real API calls:

```javascript
// In script.js — replace doLogin() with:
async function doLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  const res = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const json = await res.json();
  if (json.success) {
    localStorage.setItem('token', json.data.token);
    localStorage.setItem('user',  JSON.stringify(json.data.user));
    localStorage.setItem('center',JSON.stringify(json.data.center));
    openPortal(json.data.user.full_name, json.data.user.full_name[0]);
  } else {
    document.getElementById('login-err').textContent = json.message;
    document.getElementById('login-err').style.display = 'block';
  }
}

// Helper for authenticated requests
async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('token');
  return fetch(`http://localhost:5000${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...(options.headers || {})
    }
  }).then(r => r.json());
}
```

---

## API Reference

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | ❌ | Login with email + password |
| POST | `/api/auth/logout` | ✅ | Logout |
| GET | `/api/auth/profile` | ✅ | Get current user profile |
| POST | `/api/users/register` | ✅ | Register new staff (same center) |
| GET | `/api/users` | ✅ | Get all staff of center |

### Children

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/children` | Get all children (center filtered) |
| GET | `/api/children/<id>` | Get single child |
| POST | `/api/children` | Add child |
| PUT | `/api/children/<id>` | Update child |
| DELETE | `/api/children/<id>` | Delete child |

**Query params:** `?search=name&gender=Male`

### Beneficiaries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/beneficiaries` | Get all beneficiaries |
| POST | `/api/beneficiaries` | Add beneficiary |
| PUT | `/api/beneficiaries/<id>` | Update beneficiary |
| DELETE | `/api/beneficiaries/<id>` | Delete beneficiary |

**Query params:** `?category=Pregnant Woman&search=name`

### Stock

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | Get inventory |
| POST | `/api/stocks/add` | Add/restock item |
| POST | `/api/stocks/distribute` | Record distribution |
| GET | `/api/stocks/report` | Full stock report |
| GET | `/api/stocks/history` | Distribution history |

### Meetings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/meetings` | Get meetings |
| POST | `/api/meetings` | Create meeting |
| PUT | `/api/meetings/<id>` | Update meeting |
| DELETE | `/api/meetings/<id>` | Delete meeting |

**Query params:** `?filter=upcoming` or `?filter=past`

### Stories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories` | Get stories |
| POST | `/api/stories/upload` | Upload story |
| DELETE | `/api/stories/<id>` | Delete story |

**Query params:** `?language=Telugu&category=Moral Stories`

### Surveys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/surveys` | Get all feedback + summary |
| POST | `/api/surveys` | Submit feedback |

### Dashboard & Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Quick stats for home page |
| GET | `/api/reports/summary` | Full analytics |

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@anganwadi.gov.in | admin@123 |
| Teacher | teacher@anganwadi.gov.in | teach@123 |
| Staff | staff@anganwadi.gov.in | staff@123 |

---

## Deploy to Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add Environment Variables (same as `.env`)
6. Deploy

---

## Security Notes

- All passwords are hashed using bcrypt (never stored plain)
- JWT tokens expire after 7 days
- Every API endpoint validates `center_id` from the JWT token
- Staff can never access another center's data
- Input validation on all POST/PUT endpoints
