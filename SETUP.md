# ResQ-AI — Complete Environment Setup Guide (Gmail SMTP + Gmail API)

This guide walks you through setting up the **entire ResQ-AI environment** so that:

- The **Car Dashboard** sends a **live location request** to your personal email using
  **Gmail SMTP + App Password** (no API key).
- The **Admin Dashboard** reads/ACCEPTS those location request emails from the admin's
  Gmail inbox using the **Gmail API (OAuth)**.

**Project layout**

```
ResQ-AI/            → Car Dashboard (Streamlit) + car backend (port 5001)
ResQ-AI_Admin/      → Admin Dashboard (Streamlit) + admin backend (port 5002)
```

> **Note:** This version uses **Gmail** end-to-end. There is **no SendGrid** anywhere.

---

## Prerequisites

- **Python 3.8+** installed on Windows.
- An internet connection (for `pip install`).
- A **Gmail account** (you@gmail.com) with **2-Step Verification enabled** (needed for the App Password).
- A personal email address to *receive* the location request (can be the same Gmail).

---

## Part 1 — Create a Gmail App Password (one-time, for the CAR dashboard)

The car dashboard sends the email using Gmail SMTP. Gmail no longer allows your normal
password for SMTP — you must create a special **App Password**.

1. Go to https://myaccount.google.com/security
2. Under **"How you sign in to Google"**, make sure **2-Step Verification** is **ON**.
   (If it's off, enable it first — the App Password option won't appear otherwise.)
3. Go to https://myaccount.google.com/apppasswords
4. Under **App name**, type `ResQ-AI` and click **Create**.
5. Google shows a **16-character password** (e.g. `abcd efgh ijkl mnop`).
6. **Copy it** — this is your `GMAIL_APP_PASSWORD`. Remove the spaces.

> You will use this same App Password in both the car `.env` and the admin `.env` for sending.

---

## Part 2 — Set up the Car Dashboard environment

### 1. Create a virtual environment (recommended)
```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure credentials
```powershell
copy .env.example .env
```
Open the new `.env` file and fill in:
```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD
```

> `GMAIL_USER` = the Gmail address that sends the email.
> `GMAIL_APP_PASSWORD` = the App Password from Part 1 (no spaces).

### 4. Start the car backend
Keep this terminal open.
```powershell
python backend.py
```
Expected output: `Running on http://127.0.0.1:5001`

### 5. Start the car dashboard
Open a **second terminal**:
```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI
.venv\Scripts\activate
streamlit run Dashboard.py
```

---

## Part 3 — Set up Gmail API (OAuth) for the Admin "Accept" feature

The admin dashboard reads the location-request emails using the **Gmail API**.
This requires a **Google Cloud project** and an **OAuth client**. Do this once.

### 3.1 Enable the Gmail API
1. Go to https://console.cloud.google.com/ and create/login to a project.
2. Go to **APIs & Services → Library**.
3. Search for **Gmail API** and click **Enable**.

### 3.2 Configure the OAuth consent screen
1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External** (or Internal if using a Workspace account) → **Create**.
3. Fill in the app name (e.g. `ResQ-AI Admin`) and your email.
4. Under **Scopes**, add:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
5. Click **Save**. Skip publishing (testing mode is fine for local use).

### 3.3 Create an OAuth client ID
1. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Desktop app**.
3. Name it `ResQ-AI Admin` → **Create**.
4. Click **Download JSON** on the created client.
5. Save the downloaded file as **`client_secret.json`** inside `ResQ-AI_Admin/`.

> On first use, the admin backend will open a browser tab asking you to log into
> the Gmail account and grant permission. It then saves a `token.json` so you
> only authenticate once.

---

## Part 4 — Set up the Admin Dashboard environment

### 1. Create a virtual environment
```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI_Admin
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure credentials
```powershell
copy .env.example .env
```
Open `.env` and set:
```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD
GMAIL_CLIENT_SECRET_FILE=client_secret.json
GMAIL_TOKEN_FILE=token.json
GEMINI_API_KEY=           # optional
```

### 4. Start the admin backend
```powershell
python backend.py
```
On first run, a browser window opens for the Gmail OAuth authorization.
Expected output: `Running on http://127.0.0.1:5002`

### 5. Start the admin dashboard
In another terminal:
```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI_Admin
.venv\Scripts\activate
streamlit run Admin_Dashboard.py
```

### 6. (Optional) Enable the Gemini AI Location–Insight feature
1. Get a free Gemini API key at https://aistudio.google.com/apikey
2. In `ResQ-AI_Admin/.env`, add your key:
   ```env
   GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
   ```
3. Restart the admin dashboard.

---

## Part 5 — Test that email actually works

### Car side (send):
1. Open the **Car Dashboard** (`http://localhost:8501`).
2. In the sidebar, enter your **Registered Email** (your personal email).
3. Click **🟢 Start Monitoring**.
4. Click **📩 Send Location Request**.
5. You should see a green **"✅ Location request sent! ..."**.
6. The email with a **Google Maps** link to the vehicle's live location arrives in the inbox.

### Admin side (accept):
1. Open the **Admin Dashboard** (`http://localhost:8502`).
2. In the right panel, click **📥 Check Gmail for Location Requests**.
3. The admin's Gmail inbox is read via the Gmail API and the location-request emails are listed.
4. Click **✅ Accept & Track This Request** on one of them.

---

## Part 6 — Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Could not reach the backend` | Make sure `backend.py` is running and the terminal is open. |
| `GMAIL_USER is not set` | Add `GMAIL_USER` to `.env`. |
| `GMAIL_APP_PASSWORD is still the placeholder` | Paste your real 16-char App Password in `.env`. |
| `SMTPAuthenticationError` | App Password is wrong, or 2-Step Verification is off. Recreate it in Part 1. |
| `client_secret.json not found` | Download your OAuth client and place it in `ResQ-AI_Admin/`. |
| Browser doesn't open for Gmail auth | Run `python backend.py` in a terminal (not a service) so it can open the browser. |
| `Module 'google' not found` | Run `pip install -r requirements.txt` in the active admin venv. |

---

## Security Notes
- **Never commit `.env`**, `token.json`, or `client_secret.json` — they contain credentials.
- Keep your App Password and OAuth files secret.
- Run the backends only on your local machine (or secure them) when in development.
