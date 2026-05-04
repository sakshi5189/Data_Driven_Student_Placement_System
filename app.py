from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
conn = get_db()
conn.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT
)''')

conn.execute('''CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY,
    name TEXT,
    cgpa REAL,
    skill TEXT
)''')

conn.execute('''CREATE TABLE IF NOT EXISTS companies(
    id INTEGER PRIMARY KEY,
    name TEXT,
    min_cgpa REAL,
    skill TEXT
)''')
conn.commit()

# ---------------- EMAIL ----------------
def send_email(to_email, subject, message):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email error:", e)

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')

# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (request.form['name'], request.form['email'],
             request.form['password'], request.form['role'])
        )
        conn.commit()
        return redirect('/login')

    return render_template('register.html')

# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (request.form['email'], request.form['password'])
        ).fetchone()

        if user:
            session['user'] = user['name']
            session['role'] = user['role']

            if user['role'] == 'student':
                return redirect('/student')
            elif user['role'] == 'officer':
                return redirect('/officer')
            else:
                return redirect('/hr')

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- STUDENT ----------------
@app.route('/student')
def student():
    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE name=?",
        (session['user'],)
    ).fetchone()

    user = conn.execute(
        "SELECT * FROM users WHERE name=?",
        (session['user'],)
    ).fetchone()

    companies = conn.execute("SELECT * FROM companies").fetchall()

    notifications = []

    if student:
        for c in companies:
            if student['cgpa'] >= c['min_cgpa'] and c['skill'] in student['skill']:
                notifications.append({"company": c['name'], "status": "Eligible"})

                # SEND EMAIL
                send_email(
                    user['email'],
                    "Placement Update",
                    f"You are eligible for {c['name']}"
                )
            else:
                notifications.append({"company": c['name'], "status": "Not Eligible"})

    return render_template('student.html', student=student, notifications=notifications)

# ---------------- OFFICER ----------------
@app.route('/officer', methods=['GET','POST'])
def officer():
    conn = get_db()

    if request.method == 'POST':
        conn.execute(
            "INSERT INTO students(name,cgpa,skill) VALUES(?,?,?)",
            (request.form['name'], request.form['cgpa'], request.form['skill'])
        )
        conn.commit()

    students = conn.execute("SELECT * FROM students").fetchall()
    return render_template('officer.html', students=students)

# ---------------- HR ----------------
@app.route('/hr', methods=['GET','POST'])
def hr():
    conn = get_db()

    if request.method == 'POST':
        conn.execute(
            "INSERT INTO companies(name,min_cgpa,skill) VALUES(?,?,?)",
            (request.form['name'], request.form['cgpa'], request.form['skill'])
        )
        conn.commit()

    companies = conn.execute("SELECT * FROM companies").fetchall()
    return render_template('hr.html', companies=companies)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
