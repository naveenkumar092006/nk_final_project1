# models.py — ML Models, Machine Data & Simulation Engine

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# MACHINE DEFINITIONS
# ─────────────────────────────────────────────

MACHINES = {
    "MCH-101": {
        "name": "CNC Milling Machine",
        "installation_date": "2020-03-15",
        "last_maintenance": "2024-09-10",
        "operator": "Ravi Kumar",
        "location": "Zone A"
    },
    "MCH-102": {
        "name": "Hydraulic Press",
        "installation_date": "2019-07-22",
        "last_maintenance": "2024-08-25",
        "operator": "Suresh Nair",
        "location": "Zone B"
    },
    "MCH-103": {
        "name": "Conveyor Belt System",
        "installation_date": "2021-01-10",
        "last_maintenance": "2024-10-01",
        "operator": "Priya Sharma",
        "location": "Zone A"
    },
    "MCH-104": {
        "name": "Industrial Compressor",
        "installation_date": "2018-11-05",
        "last_maintenance": "2024-07-15",
        "operator": "Arun Patel",
        "location": "Zone C"
    },
    "MCH-105": {
        "name": "Rotary Kiln",
        "installation_date": "2017-06-30",
        "last_maintenance": "2024-06-20",
        "operator": "Meena Raj",
        "location": "Zone C"
    },
    "MCH-106": {
        "name": "Turbine Generator",
        "installation_date": "2022-02-14",
        "last_maintenance": "2024-11-01",
        "operator": "Vikram Singh",
        "location": "Zone B"
    },
}

# ─────────────────────────────────────────────
# SENSOR DATA SIMULATION
# ─────────────────────────────────────────────

def generate_sensor_history(machine_id, n_points=30):
    """Generate realistic sensor history for a machine."""
    np.random.seed(hash(machine_id) % 1000)
    # Older machines have higher baseline readings
    age_factor = {"MCH-101": 1.0, "MCH-102": 1.3, "MCH-103": 0.9,
                  "MCH-104": 1.5, "MCH-105": 1.7, "MCH-106": 0.8}
    af = age_factor.get(machine_id, 1.0)
    now = datetime.now()
    history = []
    for i in range(n_points):
        ts = now - timedelta(hours=(n_points - i) * 2)
        temp = np.random.normal(65 * af, 8)
        vib  = np.random.normal(2.5 * af, 0.5)
        pres = np.random.normal(4.0 * af, 0.6)
        hrs  = 1200 * af + i * 2 + np.random.normal(0, 10)
        # Inject anomaly spikes near end for critical machines
        if machine_id in ("MCH-104", "MCH-105") and i > 24:
            temp += np.random.uniform(15, 25)
            vib  += np.random.uniform(1.0, 2.0)
            pres += np.random.uniform(0.8, 1.5)
        history.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "temperature": round(float(np.clip(temp, 30, 120)), 1),
            "vibration":   round(float(np.clip(vib,  0.5, 8.0)), 2),
            "pressure":    round(float(np.clip(pres, 1.0, 10.0)), 2),
            "operating_hours": round(float(hrs), 0)
        })
    return history


def get_current_readings(machine_id):
    """Get the latest simulated sensor reading."""
    history = generate_sensor_history(machine_id, 30)
    return history[-1]


# ─────────────────────────────────────────────
# ML TRAINING DATA GENERATION
# ─────────────────────────────────────────────

def generate_training_data(n=2000):
    """Generate synthetic labelled training data for classification."""
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        temp = np.random.uniform(30, 120)
        vib  = np.random.uniform(0.5, 8.0)
        pres = np.random.uniform(1.0, 10.0)
        hrs  = np.random.uniform(100, 5000)
        # Failure rules
        fail = int(
            (temp > 90) or
            (vib > 5.5) or
            (pres > 7.5) or
            (hrs > 4000) or
            (temp > 75 and vib > 4.0) or
            (pres > 6.0 and hrs > 3000)
        )
        X.append([temp, vib, pres, hrs])
        y.append(fail)
    return np.array(X), np.array(y)


# ─────────────────────────────────────────────
# ML MODELS (trained once at import)
# ─────────────────────────────────────────────

_X_train, _y_train = generate_training_data()

scaler = StandardScaler()
_X_scaled = scaler.fit_transform(_X_train)

# Random Forest Classifier
rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)
rf_classifier.fit(_X_scaled, _y_train)

# Isolation Forest for anomaly detection
iso_forest = IsolationForest(contamination=0.1, random_state=42)
iso_forest.fit(_X_scaled)

# Random Forest Regressor for RUL
def _generate_rul_data(n=2000):
    np.random.seed(99)
    X, y = [], []
    for _ in range(n):
        temp = np.random.uniform(30, 120)
        vib  = np.random.uniform(0.5, 8.0)
        pres = np.random.uniform(1.0, 10.0)
        hrs  = np.random.uniform(100, 5000)
        # RUL decreases with worse readings
        rul = max(0, 60 - (temp-30)/2 - vib*3 - (pres-1)*2 - hrs/200 + np.random.normal(0, 3))
        X.append([temp, vib, pres, hrs])
        y.append(rul)
    return np.array(X), np.array(y)

_Xr, _yr = _generate_rul_data()
rul_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
rul_regressor.fit(scaler.transform(_Xr), _yr)

# Model evaluation metrics (on a held-out split)
from sklearn.model_selection import train_test_split
_Xte, _Xval, _yte, _yval = train_test_split(_X_scaled, _y_train, test_size=0.2, random_state=7)
_ypred = rf_classifier.predict(_Xval)
MODEL_METRICS = {
    "accuracy":  round(accuracy_score(_yval, _ypred) * 100, 2),
    "precision": round(precision_score(_yval, _ypred) * 100, 2),
    "recall":    round(recall_score(_yval, _ypred) * 100, 2),
    "f1":        round(f1_score(_yval, _ypred) * 100, 2),
    "confusion_matrix": confusion_matrix(_yval, _ypred).tolist(),
    "feature_importance": {
        "Temperature":      round(float(rf_classifier.feature_importances_[0]) * 100, 1),
        "Vibration":        round(float(rf_classifier.feature_importances_[1]) * 100, 1),
        "Pressure":         round(float(rf_classifier.feature_importances_[2]) * 100, 1),
        "Operating Hours":  round(float(rf_classifier.feature_importances_[3]) * 100, 1),
    }
}


# ─────────────────────────────────────────────
# PREDICTION ENGINE
# ─────────────────────────────────────────────

def predict_machine(machine_id):
    """Run full prediction pipeline for a machine."""
    reading = get_current_readings(machine_id)
    features = np.array([[
        reading["temperature"],
        reading["vibration"],
        reading["pressure"],
        reading["operating_hours"]
    ]])
    scaled = scaler.transform(features)

    # Failure probability
    fail_prob = float(rf_classifier.predict_proba(scaled)[0][1])
    health_score = round(100 - fail_prob * 100, 1)

    # Anomaly detection
    anomaly_score = iso_forest.decision_function(scaled)[0]
    is_anomaly = iso_forest.predict(scaled)[0] == -1

    # RUL prediction
    rul_days = max(0, round(float(rul_regressor.predict(scaled)[0]), 1))

    # Status
    if fail_prob > 0.60:
        status = "Critical"
    elif fail_prob > 0.30:
        status = "Warning"
    else:
        status = "Healthy"

    # Root cause deduction
    failure_type, root_cause, solutions = deduce_failure(reading)

    # Maintenance cost estimate
    cost = estimate_cost(failure_type, fail_prob)

    # Suggested maintenance date
    maint_date = None
    if fail_prob > 0.60:
        maint_date = (datetime.now() + timedelta(days=random.randint(3, 5))).strftime("%Y-%m-%d")

    return {
        "machine_id": machine_id,
        "machine_info": MACHINES[machine_id],
        "readings": reading,
        "failure_probability": round(fail_prob * 100, 1),
        "health_score": health_score,
        "status": status,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": round(float(anomaly_score), 4),
        "rul_days": rul_days,
        "failure_type": failure_type,
        "root_cause": root_cause,
        "solutions": solutions,
        "cost_estimate": cost,
        "suggested_maintenance_date": maint_date,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def deduce_failure(reading):
    """Identify root cause from dominant sensor."""
    temp = reading["temperature"]
    vib  = reading["vibration"]
    pres = reading["pressure"]
    hrs  = reading["operating_hours"]

    scores = {
        "Overheating":   temp / 90,
        "Bearing Issue": vib / 5.5,
        "Valve Blockage": pres / 7.5,
        "Wear and Tear": hrs / 4000,
    }
    dominant = max(scores, key=scores.get)

    causes = {
        "Overheating":    ("High Temperature", ["Stop machine immediately", "Check cooling system", "Inspect lubrication", "Inform maintenance team", "Allow cooldown before restart"]),
        "Bearing Issue":  ("High Vibration",   ["Inspect bearings and shaft alignment", "Check lubrication levels", "Replace worn bearings", "Perform dynamic balancing"]),
        "Valve Blockage": ("High Pressure",    ["Check relief valves", "Inspect pipelines for blockage", "Reduce operating pressure", "Replace faulty pressure sensors"]),
        "Wear and Tear":  ("High Operating Hours", ["Schedule full overhaul", "Replace consumable parts", "Perform lubrication service", "Log for predictive replacement cycle"]),
    }
    rc, sol = causes[dominant]
    return dominant, f"{rc} exceeded safe threshold", sol


def estimate_cost(failure_type, fail_prob):
    """Estimate maintenance costs based on failure type."""
    base_costs = {
        "Overheating":    {"parts": 15000, "labor": 8000},
        "Bearing Issue":  {"parts": 22000, "labor": 12000},
        "Valve Blockage": {"parts": 18000, "labor": 9000},
        "Wear and Tear":  {"parts": 30000, "labor": 15000},
    }
    bc = base_costs.get(failure_type, {"parts": 20000, "labor": 10000})
    multiplier = 1 + fail_prob
    spare  = round(bc["parts"] * multiplier)
    labor  = round(bc["labor"] * multiplier)
    total  = spare + labor
    prev   = round(total * 0.35)
    bdown  = round(total * 1.8)
    savings = bdown - total
    return {
        "spare_parts_cost": spare,
        "labor_cost": labor,
        "total_estimated": total,
        "preventive_cost": prev,
        "breakdown_repair": bdown,
        "estimated_savings": savings
    }


# ─────────────────────────────────────────────
# DAILY REPORT
# ─────────────────────────────────────────────

def generate_daily_report():
    """Generate morning startup health report for all machines."""
    report = []
    for mid in MACHINES:
        pred = predict_machine(mid)
        report.append({
            "machine_id": mid,
            "name": MACHINES[mid]["name"],
            "health_score": pred["health_score"],
            "failure_risk": pred["failure_probability"],
            "last_maintenance": MACHINES[mid]["last_maintenance"],
            "status": pred["status"],
            "recommended_action": pred["solutions"][0] if pred["solutions"] else "Continue monitoring",
            "operator": MACHINES[mid]["operator"]
        })
    return report


# ─────────────────────────────────────────────
# ANALYTICS DATA (simulated historical)
# ─────────────────────────────────────────────

def generate_analytics_data():
    """Generate simulated historical analytics data."""
    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
    failure_counts   = [random.randint(2, 8) for _ in months]
    maint_costs      = [random.randint(40000, 150000) for _ in months]
    downtime_hours   = [random.randint(5, 40) for _ in months]
    failure_types    = {"Overheating": 12, "Bearing Issue": 8, "Valve Blockage": 6, "Wear and Tear": 9}
    return {
        "months": months,
        "failure_counts": failure_counts,
        "maintenance_costs": maint_costs,
        "downtime_hours": downtime_hours,
        "failure_type_distribution": failure_types
    }


# ─────────────────────────────────────────────
# LIVE SIMULATION DATA
# ─────────────────────────────────────────────

def get_live_data(machine_id):
    """Return a single simulated live sensor snapshot with slight random drift."""
    base = get_current_readings(machine_id)
    af = {"MCH-104": 1.5, "MCH-105": 1.7}.get(machine_id, 1.0)
    return {
        "temperature": round(base["temperature"] + random.uniform(-2, 3) * af, 1),
        "vibration":   round(base["vibration"]   + random.uniform(-0.1, 0.2) * af, 2),
        "pressure":    round(base["pressure"]    + random.uniform(-0.2, 0.3) * af, 2),
        "operating_hours": base["operating_hours"] + round(random.uniform(0, 0.05), 2),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
