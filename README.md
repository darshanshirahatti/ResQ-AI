# 🚘 ResQ-AI — Smart Accident & Health Detection System

<p align="center">
  <strong>ResQ-AI 2.0 · Machine Learning Enhanced</strong><br/>
  Real-time vehicle monitoring, crash + health detection, live location tracking, and emergency email alerts
</p>

---

## 📌 Overview

**ResQ-AI** is a Machine-Learning-enhanced emergency response system built with **Streamlit** and **Flask**. It monitors a vehicle's live telemetry — speed, engine temperature, driver heart rate, and smoke level — and **alerts only when a crash is detected AND the driver is in danger**, reducing false alarms.

The system is split into **two applications** that communicate over local HTTP:

| App | Folder | Purpose | Port |
|-----|--------|---------|------|
| 🚘 **Car Dashboard** | `ResQ-AI/` | In-vehicle monitoring UI + ML prediction + location emailing | 5001 (backend) / 8501 (Streamlit) |
| 🛰️ **Admin Dashboard** | `ResQ-AI_Admin/` | Control-room live tracking, emergency alerts, Gemini AI insights, Gmail request accepting | 5002 (backend) / 8502 (Streamlit) |

> **Email:** This version uses **Gmail end-to-end** — **Gmail SMTP + App Password** for *sending* location emails, and the **Gmail API (OAuth)** for *reading/accepting* location requests on the admin side. There is no SendGrid.

---

## ✨ Features

### Car Dashboard (`ResQ-AI/Dashboard.py`)
- **Live telemetry monitoring** — speed, engine temp, heart rate, smoke level (with simulated sensor data).
- **ML-based accident prediction** using a trained **Random Forest** classifier.
- **Anomaly detection** using an **Isolation Forest** model.
- **Driver health trend analysis** (detects rapid HR increase, decrease, or high variability).
- **Configurable alert thresholds** (crash speed, critical HR, temp, smoke).
- **Emergency alert triggering** — only when a crash AND a person-in-danger condition co-occur.
- **Browser geolocation** with embedded **Google Maps** live view.
- **Live location request emailing** to a registered recipient via the Flask backend.
- **Pushes live location** to the Admin backend for real-time tracking.
- Real-time sensor charts, movement trail map, and emergency alert history.
- **Crash simulation** button for testing/demo purposes.

### Admin Dashboard (`ResQ-AI_Admin/Admin_Dashboard.py`)
- **Live vehicle tracking** — see which vehicles are reporting in real time.
- **Live map** of a selected vehicle's current location.
- **Movement trail / history** visualization.
- **Live sensor metrics** (speed, temp, heart, smoke) and impact detection.
- **Emergency alert feed**.
- **Email current location** to the admin's registered email.
- **Accept location requests** by reading the admin's Gmail inbox via the **Gmail API (OAuth)**.
- **Gemini AI location insights** — generates a human-readable safety analysis of a received location.

---

## 🏗️ Architecture

```
┌─────────────────────────────┐          ┌──────────────────────────────┐
│    🚘 CAR DASHBOARD          │          │    🛰️ ADMIN DASHBOARD         │
│  (ResQ-AI/) Streamlit  8501  │          │ (ResQ-AI_Admin/) Streamlit 8502│
│                              │          │                              │
│  Dashboard.py                │          │  Admin_Dashboard.py          │
│   - ML prediction            │          │   - Live tracking            │
│   - geolocation              │          │   - Gemini AI insights       │
│   - push /update-location ───┼───HTTP──▶│   - Gmail API accept         │
│   - send location request ───┼───HTTP──▶│                              │
└───────────────┬──────────────┘          └──────────────┬───────────────┘
                │                                       │
        ┌───────▼────────┐                      ┌───────▼────────┐
        │  CAR BACKEND    │                      │ ADMIN BACKEND  │
        │  backend.py     │                      │  backend.py    │
        │  Flask :5001    │                      │  Flask :5002    │
        │  Gmail SMTP     │                      │  In-memory store│
        │  (sends email)  │                      │  Gmail API OAuth│
        └─────────────────┘                      └─────────────────┘
```

**Data flow:**

1. The **Car Dashboard** reads live telemetry (simulated) and ML models predict crash risk/anomalies.
2. It **pushes** its live location + sensor data to the Admin backend (`POST /update-location`).
3. On request, the Car backend emails the live location to the recipient via **Gmail SMTP**.
4. The **Admin Dashboard** reads the latest vehicle data from the Admin backend.
5. The Admin can **read incoming location-request emails** via the **Gmail API** and accept them.
6. Optionally, the Admin generates an **AI location insight** with the **Gemini API**.

---

## 🧠 Machine Learning Models

| Model | Type | Used For |
|-------|------|----------|
| `AccidentPredictor` | Random Forest Classifier | Predicts the probability of an accident from speed, temp, heart, smoke, impact |
| `AnomalyDetector` | Isolation Forest | Detects abnormal environmental sensor patterns |
| `HealthPredictor` | Linear-trend / statistical analysis | Detects rapid HR increase, decrease, and high variability |

> **Note:** Models are trained on **synthetic data** at startup for demonstration purposes. In a production deployment, they should be trained on real telemetry.

---

## 🛠️ Tech Stack

- **Frontend / UI:** Streamlit
- **Backend:** Flask + Flask-CORS
- **ML:** scikit-learn (RandomForest, IsolationForest), NumPy, Pandas
- **Email (sending):** Gmail SMTP + App Password (`smtplib`)
- **Email (reading):** Google Gmail API (OAuth 2.0) — `google-api-python-client`
- **AI Insights:** Google Gemini API (`google-generativeai`)
- **Environment:** `python-dotenv`
- **Geolocation:** Browser geolocation via `streamlit-javascript`

---

## 📁 Project Structure

```
ResQ-AI/
├── README.md                     ← This file
├── SETUP.md                      ← Environment setup guide (Gmail SMTP + Gmail API)
├── ResQ-AI/                      ← Car Dashboard application
│   ├── Dashboard.py              ← Car Streamlit UI (ML + monitoring)
│   ├── backend.py                ← Car Flask backend (port 5001, Gmail SMTP)
│   ├── requirements.txt
│   ├── .env.example              ← Template for car credentials
│   ├── .gitignore
│   ├── IDEATHON-2025_ResQ-AI.pptx
│   ├── ResQ-AI_Ideathon_Presentation.pptx
│   └── ResQ-AI new.docx
└── ResQ-AI_Admin/                ← Admin Dashboard application
    ├── Admin_Dashboard.py        ← Admin Streamlit UI (tracking, Gemini, Gmail API)
    ├── backend.py                ← Admin Flask backend (port 5002, Gmail API + SMTP)
    ├── requirements.txt
    ├── .env.example              ← Template for admin credentials
    └── .gitignore
```

---

## ✅ Prerequisites

- **Python 3.8+** installed on Windows.
- An internet connection (for `pip install`).
- A **Gmail account** with **2-Step Verification enabled** (needed for the App Password).
- A personal email address to *receive* the location request (can be the same Gmail).
- (Optional) A **Gemini API key** for the AI location-insight feature.
- (Optional) A **Google Cloud project** with the Gmail API enabled and an **OAuth client** for the Admin "Accept" feature.

---

## 🚀 Setup & Installation

> 📄 A detailed, step-by-step guide lives in [`SETUP.md`](SETUP.md). The summary below covers both apps.

### Step 1 — Create a Gmail App Password (one-time, for sending)

1. Go to https://myaccount.google.com/security and enable **2-Step Verification**.
2. Go to https://myaccount.google.com/apppasswords.
3. Create an app named `ResQ-AI` and **copy the 16-character password** (remove spaces).
4. This is your `GMAIL_APP_PASSWORD`.

### Step 2 — Set up the Car Dashboard

```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit the new `.env`:
```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD
```

Start the car backend (terminal 1):
```powershell
python backend.py          # → Running on http://127.0.0.1:5001
```

Start the car dashboard (terminal 2):
```powershell
streamlit run Dashboard.py # → http://localhost:8501
```

### Step 3 — Set up Gmail API (OAuth) for the Admin "Accept" feature

1. At https://console.cloud.google.com, create a project and **enable the Gmail API**.
2. Configure the **OAuth consent screen** (add `gmail.readonly` and `gmail.send` scopes).
3. Create an **OAuth client ID** (Application type: **Desktop app**) and **Download JSON**.
4. Save the downloaded file as **`client_secret.json`** inside `ResQ-AI_Admin/`.

> On first run, the admin backend opens a browser to authorize the Gmail account and then caches a `token.json` so you only authenticate once.

### Step 4 — Set up the Admin Dashboard

```powershell
cd C:\Users\darsh\ResQ-AI\ResQ-AI_Admin
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit the new `.env`:
```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD
GMAIL_CLIENT_SECRET_FILE=client_secret.json
GMAIL_TOKEN_FILE=token.json
GEMINI_API_KEY=             # optional
```

Start the admin backend (terminal 3):
```powershell
python backend.py          # → Running on http://127.0.0.1:5002
```

Start the admin dashboard (terminal 4):
```powershell
streamlit run Admin_Dashboard.py # → http://localhost:8502
```

### Step 5 — (Optional) Enable Gemini AI Location Insights

1. Get a free Gemini API key at https://aistudio.google.com/apikey.
2. Add it to `ResQ-AI_Admin/.env`:
   ```env
   GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
   ```
3. Restart the admin dashboard.

---

## 🔑 Environment Variables

### `ResQ-AI/.env` (Car)
| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_USER` | Gmail address that sends emails | ✅ |
| `GMAIL_APP_PASSWORD` | 16-char App Password (no spaces) | ✅ |

### `ResQ-AI_Admin/.env` (Admin)
| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_USER` | Gmail address used for sending | ✅ |
| `GMAIL_APP_PASSWORD` | 16-char App Password (no spaces) | ✅ |
| `GMAIL_CLIENT_SECRET_FILE` | OAuth client JSON filename (default `client_secret.json`) | ✅ |
| `GMAIL_TOKEN_FILE` | Cached OAuth token filename (default `token.json`) | ✅ |
| `GEMINI_API_KEY` | Gemini API key for AI location insights | ❌ (optional) |

> ⚠️ **Never commit** `.env`, `client_secret.json`, or `token.json` — they contain credentials. They are already in `.gitignore`.

---

## 🧪 Usage & Testing

### Car side (send a location request)
1. Open the **Car Dashboard** (`http://localhost:8501`).
2. In the sidebar, enter your **Registered Email**.
3. Click **🟢 Start Monitoring**.
4. Click **📩 Send Location Request**.
5. A green **"✅ Location request sent!"** message appears, and the email with a **Google Maps** link arrives in the inbox.

### Admin side (accept & track)
1. Open the **Admin Dashboard** (`http://localhost:8502`).
2. In the right panel, click **📥 Check Gmail for Location Requests**.
3. The Gmail API reads location-request emails from the admin's inbox.
4. Click **✅ Accept & Track This Request** to start tracking that vehicle.

### Demo / Testing
- Use the **⚠️ Simulate Crash + Emergency** button on the car dashboard to force an emergency alert.
- Use **🧠 Generate AI Location Insight** on the admin dashboard to test Gemini analysis.

---

## 📡 API Reference

### Car Backend (`http://127.0.0.1:5001`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/send-location-request` | Emails the vehicle's live location via Gmail SMTP. Body: `to_email`, `latitude`, `longitude`, `vehicle_number`, `driver_name` |

### Admin Backend (`http://127.0.0.1:5002`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + vehicle count |
| `POST` | `/update-location` | Car dashboard pushes live location + sensor data |
| `GET` | `/vehicles` | List all vehicles reporting |
| `GET` | `/current-location?vehicle=...` | Latest live location for a vehicle |
| `GET` | `/location-history?vehicle=...` | Movement trail/history for a vehicle |
| `GET` | `/emergency-alerts?vehicle=...` | Emergency alerts (all or per vehicle) |
| `POST` | `/send-location-request` | Send current location to a recipient email |
| `GET` | `/gmail-requests?max=...` | Read location-request emails from admin Gmail via the Gmail API |

---

## 🩺 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Could not reach the backend` | Make sure `backend.py` is running and its terminal is open. |
| `GMAIL_USER is not set` | Add `GMAIL_USER` to `.env`. |
| `GMAIL_APP_PASSWORD is still the placeholder` | Paste your real 16-char App Password in `.env`. |
| `SMTPAuthenticationError` | App Password is wrong, or 2-Step Verification is off. Recreate it. |
| `client_secret.json not found` | Download your OAuth client and place it in `ResQ-AI_Admin/`. |
| Browser doesn't open for Gmail auth | Run `python backend.py` in a terminal (not as a service). |
| `Module 'google' not found` | Run `pip install -r requirements.txt` in the active admin venv. |
| `Gemini API error` | Verify `GEMINI_API_KEY` is set and valid in `ResQ-AI_Admin/.env`. |
| Email not arriving | Check the **spam** folder and confirm the recipient email is correct. |

---

## 🔒 Security Notes

- **Never commit** `.env`, `token.json`, or `client_secret.json` — they contain credentials.
- Keep your App Password and OAuth files secret.
- For production, restrict the Google OAuth app to **testing mode** or publish it properly, and protect the backends (they run with `debug=True` locally).
- Use restricted OAuth scopes in production rather than full access.
- The ML models are trained on synthetic demo data — retrain on real telemetry for production use.

---

## 📄 License & Credits

Built for the **IDEATHON-2025** hackathon. This project is a demonstration of an AI-powered emergency response and fleet-tracking system.

---

Happy building! 🚘🛰️
