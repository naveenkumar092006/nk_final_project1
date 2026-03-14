# app.py — Main Flask Application
# Industrial Predictive Maintenance System

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
import json, os, io
from datetime import datetime

from config import Config
from auth import init_db, get_user_by_id, verify_user, get_all_users, create_user, delete_user, User
from models import (
    MACHINES, predict_machine, generate_daily_report,
    generate_analytics_data, get_live_data, get_current_readings,
    generate_sensor_history, MODEL_METRICS
)

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
init_db()

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access the dashboard."

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))


# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = verify_user(username, password)
        if user:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    # Determine accessible machines
    if current_user.role == 'operator' and current_user.assigned_machine:
        machine_ids = [current_user.assigned_machine]
    else:
        machine_ids = list(MACHINES.keys())

    daily_report = generate_daily_report()
    predictions = {mid: predict_machine(mid) for mid in machine_ids}
    selected_id = request.args.get('machine', machine_ids[0])
    selected_pred = predictions.get(selected_id, predictions[machine_ids[0]])
    history = generate_sensor_history(selected_id)

    return render_template('dashboard.html',
        machines=MACHINES,
        machine_ids=machine_ids,
        predictions=predictions,
        selected_id=selected_id,
        selected_pred=selected_pred,
        history=history,
        daily_report=daily_report,
        model_metrics=MODEL_METRICS,
        now=datetime.now().strftime("%A, %d %B %Y — %H:%M")
    )


# ─────────────────────────────────────────────
# MACHINE SEARCH
# ─────────────────────────────────────────────

@app.route('/search')
@login_required
def search():
    machine_id = request.args.get('machine_id', '').upper().strip()
    result = None
    history = None
    if machine_id:
        if machine_id in MACHINES:
            result = predict_machine(machine_id)
            history = generate_sensor_history(machine_id)
        else:
            flash(f'Machine ID "{machine_id}" not found.', 'warning')
    return render_template('search.html', result=result, history=history,
                           machines=MACHINES, query=machine_id)


# ─────────────────────────────────────────────
# ANALYTICS DASHBOARD
# ─────────────────────────────────────────────

@app.route('/analytics')
@login_required
def analytics():
    if not (current_user.can('view_costs') or current_user.can('generate_reports')):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    data = generate_analytics_data()
    all_preds = {mid: predict_machine(mid) for mid in MACHINES}
    return render_template('analytics.html', analytics=data, predictions=all_preds)


# ─────────────────────────────────────────────
# USER MANAGEMENT (Admin only)
# ─────────────────────────────────────────────

@app.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard'))
    users = get_all_users()
    return render_template('users.html', users=users, machines=MACHINES)


@app.route('/users/create', methods=['POST'])
@login_required
def create_user_route():
    if current_user.role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    username = request.form.get('username')
    password = request.form.get('password')
    role     = request.form.get('role')
    email    = request.form.get('email')
    machine  = request.form.get('assigned_machine') or None
    ok, msg  = create_user(username, password, role, email, machine)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('manage_users'))


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user_route(user_id):
    if current_user.role != 'admin':
        return jsonify({"success": False}), 403
    delete_user(user_id)
    flash('User deleted.', 'success')
    return redirect(url_for('manage_users'))


# ─────────────────────────────────────────────
# PDF REPORT GENERATOR
# ─────────────────────────────────────────────

@app.route('/report/pdf/<machine_id>')
@login_required
def download_pdf(machine_id):
    if machine_id not in MACHINES:
        flash('Machine not found.', 'warning')
        return redirect(url_for('dashboard'))
    pred = predict_machine(machine_id)
    pdf_bytes = generate_pdf_report(pred)
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=f"Health_Report_{machine_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
        as_attachment=True,
        mimetype='application/pdf'
    )


def generate_pdf_report(pred):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=22, textColor=colors.HexColor('#00d4ff'),
                                  spaceAfter=4, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('sub', fontSize=11, textColor=colors.HexColor('#888888'), spaceAfter=12)
    body_style = ParagraphStyle('body', fontSize=10, textColor=colors.black, spaceAfter=6)
    section_style = ParagraphStyle('section', fontSize=13, textColor=colors.HexColor('#0a5c9e'),
                                   spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold')

    story.append(Paragraph("🏭 Industrial Predictive Maintenance System", header_style))
    story.append(Paragraph(f"Machine Health Report — Generated {datetime.now().strftime('%d %B %Y, %H:%M')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#00d4ff')))
    story.append(Spacer(1, 0.4*cm))

    # Machine Info
    story.append(Paragraph("Machine Information", section_style))
    info_data = [
        ["Machine ID", pred["machine_id"]],
        ["Machine Name", pred["machine_info"]["name"]],
        ["Operator", pred["machine_info"]["operator"]],
        ["Location", pred["machine_info"]["location"]],
        ["Installation Date", pred["machine_info"]["installation_date"]],
        ["Last Maintenance", pred["machine_info"]["last_maintenance"]],
    ]
    t = Table(info_data, colWidths=[5*cm, 12*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f4fd')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Health Status
    story.append(Paragraph("Health & Prediction Results", section_style))
    status_color = {'Healthy': '#2ecc71', 'Warning': '#f39c12', 'Critical': '#e74c3c'}.get(pred['status'], '#888')
    health_data = [
        ["Health Score", f"{pred['health_score']}%"],
        ["Failure Probability", f"{pred['failure_probability']}%"],
        ["Machine Status", pred['status']],
        ["Anomaly Detected", "YES" if pred['is_anomaly'] else "NO"],
        ["Remaining Useful Life", f"{pred['rul_days']} days"],
    ]
    if pred.get('suggested_maintenance_date'):
        health_data.append(["Suggested Maintenance", pred['suggested_maintenance_date']])
    t2 = Table(health_data, colWidths=[6*cm, 11*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#fff3e0')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # Failure Deduction
    story.append(Paragraph("Failure Deduction & Recommendations", section_style))
    story.append(Paragraph(f"<b>Failure Type:</b> {pred['failure_type']}", body_style))
    story.append(Paragraph(f"<b>Root Cause:</b> {pred['root_cause']}", body_style))
    story.append(Paragraph("<b>Recommended Actions:</b>", body_style))
    for i, sol in enumerate(pred['solutions'], 1):
        story.append(Paragraph(f"  {i}. {sol}", body_style))
    story.append(Spacer(1, 0.4*cm))

    # Cost Estimate
    c = pred['cost_estimate']
    story.append(Paragraph("Maintenance Cost Estimation (INR)", section_style))
    cost_data = [
        ["Spare Parts Cost",       f"₹{c['spare_parts_cost']:,}"],
        ["Labor Cost",             f"₹{c['labor_cost']:,}"],
        ["Total Estimated Cost",   f"₹{c['total_estimated']:,}"],
        ["Preventive Maint. Cost", f"₹{c['preventive_cost']:,}"],
        ["Breakdown Repair Cost",  f"₹{c['breakdown_repair']:,}"],
        ["Estimated Savings",      f"₹{c['estimated_savings']:,}"],
    ]
    t3 = Table(cost_data, colWidths=[8*cm, 9*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f8e8')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,5), (-1,5), colors.HexColor('#27ae60')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f9fff9')]),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t3)

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph("Confidential — Industrial Predictive Maintenance System | Factory Intelligence Platform",
                           ParagraphStyle('footer', fontSize=8, textColor=colors.grey, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.route('/api/live-data')
@login_required
def api_live_data():
    machine_id = request.args.get('machine_id', 'MCH-101')
    if machine_id not in MACHINES:
        return jsonify({"error": "Machine not found"}), 404
    data = get_live_data(machine_id)
    pred = predict_machine(machine_id)
    data.update({
        "failure_probability": pred["failure_probability"],
        "health_score": pred["health_score"],
        "rul_days": pred["rul_days"],
        "status": pred["status"],
        "is_anomaly": pred["is_anomaly"]
    })
    return jsonify(data)


@app.route('/api/predictions')
@login_required
def api_predictions():
    preds = {mid: predict_machine(mid) for mid in MACHINES}
    return jsonify(preds)


@app.route('/api/machine/<machine_id>')
@login_required
def api_machine(machine_id):
    if machine_id not in MACHINES:
        return jsonify({"error": "Not found"}), 404
    pred = predict_machine(machine_id)
    history = generate_sensor_history(machine_id)
    return jsonify({"prediction": pred, "history": history})


@app.route('/api/send-alert/<machine_id>', methods=['POST'])
@login_required
def send_alert(machine_id):
    """Send email alert for critical machine (simulated if no SMTP configured)."""
    pred = predict_machine(machine_id)
    subject = f"🚨 CRITICAL ALERT: {machine_id} — {pred['failure_type']}"
    body = f"""
INDUSTRIAL ALERT — {datetime.now().strftime('%Y-%m-%d %H:%M')}

Machine ID:       {machine_id}
Machine Name:     {pred['machine_info']['name']}
Failure Type:     {pred['failure_type']}
Failure Risk:     {pred['failure_probability']}%
Health Score:     {pred['health_score']}%
Root Cause:       {pred['root_cause']}

RECOMMENDED ACTIONS:
{chr(10).join(f"  - {s}" for s in pred['solutions'])}

Estimated Cost:   ₹{pred['cost_estimate']['total_estimated']:,}

— Automated Predictive Maintenance System
"""
    # Console simulation
    print(f"\n{'='*60}\n📧 SIMULATED EMAIL ALERT\n{body}\n{'='*60}")
    try:
        msg = Message(subject, recipients=[Config.ALERT_RECIPIENT])
        msg.body = body
        mail.send(msg)
        return jsonify({"success": True, "method": "email"})
    except Exception:
        return jsonify({"success": True, "method": "console_simulation",
                        "note": "Email not configured — alert printed to console"})


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🏭  Industrial Predictive Maintenance System")
    print("  🌐  http://127.0.0.1:5000")
    print("  👤  Default login: admin / Admin@123")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
