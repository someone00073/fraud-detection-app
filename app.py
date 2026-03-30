import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file)
from werkzeug.security import generate_password_hash, check_password_hash

import pandas as pd

# 🔥 IMPORT FROM YOUR model.py
from model import load_model, encode_input

import smtplib
from email.mime.text import MIMEText

# ---------------- EMAIL ----------------
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER  

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Email error:", e)

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "secret123"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "database.db")
OUTPUT_PATH = os.path.join(BASE_DIR, "output.csv")

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email_id TEXT,
            created_at TEXT,
            last_login TEXT,
            status TEXT DEFAULT 'active'
        )
        """)
        conn.commit()
 

        # create admin
        exists = conn.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not exists:
            conn.execute("""
            INSERT INTO users (username, password, email_id, created_at, status)
            VALUES (?, ?, ?, ?, ?)
            """, (
                "admin",
                generate_password_hash("admin123"),
                EMAIL_USER,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active"
            ))
            conn.commit()
init_db()  

# ---------------- AUTH DECORATORS ----------------
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "username" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get("username") != "admin":
            return redirect("/dashboard")
        return f(*args, **kwargs)
    return wrap

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if not user or not check_password_hash(user["password"], password):
            flash("Invalid login", "error")
            return render_template("login.html")

        if user["status"] == "blocked":
            flash("Account blocked", "error")
            return render_template("login.html")

        # update last login
        with get_db() as conn:
            conn.execute("UPDATE users SET last_login=? WHERE username=?",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            conn.commit()

        session["username"] = username
        session["is_admin"] = (username == "admin")

        try:
            send_email("Login Alert", f"{username} logged in")
        except Exception as e:
            print("Email failed:", e)

        return redirect("/admin" if username == "admin" else "/dashboard")

    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        try:
            with get_db() as conn:
                conn.execute("""
                INSERT INTO users (username, password, email_id, created_at, status)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    username,
                    generate_password_hash(password),
                    email,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "active"
                ))
                conn.commit()

                try:
                    send_email("Login Alert", f"{username} logged in")
                except Exception as e:
                    print("Email failed:", e)
            return redirect("/login")

        except:
            flash("Username exists", "error")

    return render_template("signup.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.get_json()

        # 🔥 RULE CHECK FIRST
        amount = float(data.get('amount', 0))
        hour = float(data.get('hour', 0))
        new_device = int(data.get('new_device', 0))

        if amount > 3000 or hour < 5 or new_device == 1:
            return jsonify({
                'result': 1,
                'confidence': 95   # fixed confidence for rule
            })

        # 🔥 MODEL
        model, encoders = load_model()
        features = encode_input(data, encoders)

        pred = int(model.predict(features)[0])

        # ✅ ADD THIS HERE
        prob = model.predict_proba(features)[0][1]

        return jsonify({
            'result': pred,
            'confidence': round(prob * 100, 2)
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({'error': 'Prediction failed'}), 500


@app.route("/upload_csv", methods=["POST"])
@login_required
def upload_csv():
    file = request.files["file"]

    if file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    model, encoders = load_model()

    results = []
    for _, row in df.iterrows():
        features = encode_input(row.to_dict(), encoders)
        pred = int(model.predict(features)[0])
        results.append(pred)

    df["fraud"] = results
    df.to_csv(OUTPUT_PATH, index=False)

    return render_template("csv_result.html", rows=df.to_dict(orient="records"))

# ---------------- DOWNLOAD ----------------
@app.route("/download_output")
@login_required
def download_output():
    return send_file(OUTPUT_PATH, as_attachment=True)

# ---------------- ADMIN ----------------
@app.route("/admin")
@login_required
@admin_required
def admin():
    with get_db() as conn:
        users = conn.execute("SELECT * FROM users WHERE username!='admin'").fetchall()
    return render_template("admin.html", users=users)

# ---------------- BLOCK USER ----------------
@app.route("/admin/toggle_block", methods=["POST"])
@login_required
@admin_required
def toggle_block():
    username = request.form["username"]

    with get_db() as conn:
        user = conn.execute("SELECT status FROM users WHERE username=?", (username,)).fetchone()
        new_status = "blocked" if user["status"] == "active" else "active"

        conn.execute("UPDATE users SET status=? WHERE username=?", (new_status, username))
        conn.commit()

    return redirect("/admin")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    load_model()
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))