# 🏭 PredictMaint Pro — Industrial Predictive Maintenance System

A complete, enterprise-grade predictive maintenance web system for college competition demos.
Runs fully locally with simulated data. No paid external services required.

---

## 🚀 Quick Start (VS Code)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

---

## 👤 Default Login Credentials

| Username   | Password      | Role                 |
|------------|---------------|----------------------|
| admin      | Admin@123     | Admin (full access)  |
| engineer1  | Engineer@123  | Maintenance Engineer |
| operator1  | Operator@123  | Operator (MCH-101)   |
| manager1   | Manager@123   | Manager              |

---

## 📁 Project Structure

```
predictive_maintenance/
│
├── app.py              ← Main Flask application (routes, PDF, API)
├── models.py           ← ML models, simulation engine, predictions
├── auth.py             ← Role-based auth, SQLite user management
├── config.py           ← App configuration, thresholds, SMTP settings
├── requirements.txt    ← Python dependencies
├── run.sh              ← Quick-start shell script
│
├── templates/
│   ├── base.html       ← Shared layout (navbar, sidebar)
│   ├── login.html      ← Login page
│   ├── dashboard.html  ← Main dashboard (all features)
│   ├── search.html     ← Machine search & detail
│   ├── analytics.html  ← Analytics dashboard (/analytics)
│   └── users.html      ← User management (admin only)
│
├── static/
│   ├── css/main.css    ← Dark industrial theme
│   └── js/main.js      ← Charts, gauge, alarm, simulation
│
└── instance/
    └── factory.db      ← SQLite DB (auto-created on first run)
```

---

## ✨ Features Implemented

### Core
- ✅ 6 simulated industrial machines with full sensor data
- ✅ Random Forest Classifier for failure prediction
- ✅ Isolation Forest for anomaly detection
- ✅ RUL (Remaining Useful Life) prediction via RandomForestRegressor
- ✅ Root cause deduction (Temperature / Vibration / Pressure / Hours)
- ✅ Morning startup daily health report

### Dashboard
- ✅ Dark industrial theme with animated gauges
- ✅ Real-time sensor trend charts (Temperature, Vibration, Pressure)
- ✅ Health score bar chart for all machines
- ✅ Red failure points + yellow anomaly points highlighted on charts
- ✅ Auto-refresh every 5 seconds

### Alerts
- ✅ Flashing red critical alert cards
- ✅ Web Audio API alarm sound (browser, no external files needed)
- ✅ Email alert (SMTP or console simulation)

### Enterprise Features
- ✅ Smart Maintenance Planner with cost estimation (INR)
- ✅ Role-based authentication (Admin / Engineer / Operator / Manager)
- ✅ PDF report generator (ReportLab)
- ✅ Explainable AI feature importance chart
- ✅ Live simulation mode (2-second updates via AJAX)
- ✅ Analytics dashboard: monthly failures, failure types, cost trend, downtime
- ✅ Machine search with full sensor history
- ✅ User management panel (Admin)

### Model Evaluation
- ✅ Accuracy, Precision, Recall, F1 Score displayed
- ✅ Confusion Matrix (TP/TN/FP/FN)
- ✅ Feature importance horizontal bar chart

---

## ⚙️ Configuration

Edit `config.py` to set:
- `MAIL_USERNAME` / `MAIL_PASSWORD` — for real email alerts
- `CRITICAL_FAILURE_PROB` — threshold for critical status (default 0.60)
- `DASHBOARD_REFRESH_MS` — auto-refresh interval (default 5000ms)

---

## 🧠 ML Models Used

| Model | Purpose |
|---|---|
| `RandomForestClassifier` | Failure probability prediction |
| `IsolationForest` | Anomaly detection |
| `RandomForestRegressor` | Remaining Useful Life (RUL) |
| `StandardScaler` | Feature normalization |

---

## 🏆 Machines Monitored

| ID      | Machine Name          | Zone   |
|---------|-----------------------|--------|
| MCH-101 | CNC Milling Machine   | Zone A |
| MCH-102 | Hydraulic Press       | Zone B |
| MCH-103 | Conveyor Belt System  | Zone A |
| MCH-104 | Industrial Compressor | Zone C |
| MCH-105 | Rotary Kiln           | Zone C |
| MCH-106 | Turbine Generator     | Zone B |

---

Built for college competition demo purposes. All data is simulated.
