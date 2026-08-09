# ResQ-AI — Email Backend Setup Guide (SendGrid API)

This guide explains how to set up **SendGrid** so the ResQ-AI dashboard can actually send
the location request email to your personal email address.

> **Why this approach?** The original dashboard used a `mailto:` link, which only opens
> your email app with a draft — it never *sends* anything. We replaced that with a small
> Flask backend that sends the email via the **SendGrid Email API**. This uses an **API Key**
> (free tier: ~100 emails/day).

---

## Files Added / Changed

| File | Purpose |
|------|---------|
| `backend.py` | Flask API (`POST /send-location-request`) that emails the location via SendGrid |
| `requirements.txt` | Python dependencies (now includes `sendgrid`) |
| `.env.example` | Template for your credentials (copy to `.env`) |
| `.env` | **Your real credentials — never commit this file** |
| `.gitignore` | Prevents `.env` and Python junk from being committed |
| `Dashboard.py` | Calls the backend (HTTP POST) instead of the `mailto:` link |

---

## Step-by-Step Setup

### Step 1 — Create a SendGrid account and API key
1. Go to https://signup.sendgrid.com and create a **free** account.
2. Complete the signup (verify your email + basic sender identity / "Single Sender").
3. In the dashboard, go to **Settings → API Keys**.
4. Click **Create API Key**, give it a name (e.g. `ResQ-AI`), and choose **Full Access**.
5. Click **Create & View**. **Copy the API key now** — it starts with `SG.` and is shown
   only once. This is your `SENDGRID_API_KEY`.

### Step 2 — Verify / add a Sender (From email)
SendGrid requires a **verified sender email** before you can send mail.
1. Go to **Settings → Sender Authentication** (or **Marketing → Senders**).
2. Click **Verify a Single Sender**.
3. Enter the **"from" email address** (this is the sender that appears in the email; it
   can be your personal Gmail, e.g. `you@gmail.com`) and fill in the required details.
4. SendGrid emails you a **verification link** — click it to verify.
5. This verified email is your `FROM_EMAIL`.

### Step 3 — Install Python dependencies
Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

> Tip: Use a virtual environment:
> ```bash
> python -m venv .venv
> .venv\Scripts\activate        # Windows
> pip install -r requirements.txt
> ```

### Step 4 — Create your `.env` file
Copy the template and fill in your real values:

```bash
copy .env.example .env     # Windows
```

Then edit `.env`:

```env
# Your SendGrid API Key (starts with "SG.")
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# The verified sender email you created in SendGrid (Step 2)
FROM_EMAIL=you@gmail.com
```

> **Important:** Replace `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your **real** API key,
> and set `FROM_EMAIL` to your **verified** sender email.

### Step 5 — Run the backend
In one terminal:

```bash
python backend.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5001
```

### Step 6 — Run the dashboard
In a second terminal:

```bash
streamlit run Dashboard.py
```

### Step 7 — Test it
1. In the dashboard sidebar, enter your **Registered Email** (your personal email).
2. Click **Start Monitoring**.
3. Click **📍 Request Live Location Access** (allow browser permission).
4. Click **📩 Send Location Request**.
5. You should see a green **"✅ Location request sent! Email sent successfully via SendGrid."** message.
6. Check your personal email — you'll receive the location request with a Google Maps link.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `Could not reach the backend...` | `backend.py` isn't running. Start it (`python backend.py`) and keep it open. |
| `SENDGRID_API_KEY is not set` | Your `.env` file is missing or empty. Create it from `.env.example`. |
| `SENDGRID_API_KEY is still the placeholder` | You haven't replaced the fake key. Paste your real `SG.` key into `.env`. |
| `FROM_EMAIL is still the placeholder` | Set `FROM_EMAIL` to your **verified** sender email created in SendGrid. |
| `SendGrid returned status 401` | Invalid API key. Recreate it in SendGrid and update `.env`. |
| `SendGrid returned status 403` | The `FROM_EMAIL` isn't verified. Complete Step 2 (Single Sender verification). |
| Email not arriving | Check **spam** folder. Also confirm the recipient is your personal email. |

---

## Security Notes
- **Never commit `.env`.** It's already in `.gitignore`.
- Restrict the API key to **Full Access** only for development; use restricted scopes in production.
- If hosting publicly, restrict access to the backend and use environment variables
  (not hard-coded credentials) in production.

---

## Bonus: Admin Dashboard (optional)
The `ResQ-AI_Admin` folder has its own backend (`ResQ-AI_Admin/backend.py`) that also
sends location emails via SendGrid. It uses the **same** two variables in its own `.env`:
- `ResQ-AI_Admin/.env` → `SENDGRID_API_KEY` and `FROM_EMAIL`

Run it on port `5002`:
```bash
cd ResQ-AI_Admin
python backend.py
