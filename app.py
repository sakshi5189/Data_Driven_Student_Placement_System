from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cgpa REAL,
        skill TEXT
    )''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS companies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        min_cgpa REAL,
        skill TEXT
    )''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS sent_emails(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        company_name TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ---------- EMAIL ----------
def send_email(to_email, subject, message):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        print("EMAIL NOT CONFIGURED")
        return

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("EMAIL SENT")

    except Exception as e:
        print("EMAIL ERROR:", e)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return redirect('/login')

# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (request.form['name'], request.form['email'],
                 request.form['password'], request.form['role'])
            )
            conn.commit()
        except:
            return "User already exists"

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

        else:
            return "Invalid Login"

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- STUDENT ----------
@app.route('/student')
def student():
    if 'user' not in session:
        return redirect('/login')

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
                status = "Eligible"

                # check if email already sent
                check = conn.execute(
                    "SELECT * FROM sent_emails WHERE student_name=? AND company_name=?",
                    (student['name'], c['name'])
                ).fetchone()

                if not check:
                    send_email(
                        user['email'],
                        "Placement Eligibility",
                        f"You are eligible for {c['name']}"
                    )

                    conn.execute(
                        "INSERT INTO sent_emails(student_name,company_name) VALUES(?,?)",
                        (student['name'], c['name'])
                    )
                    conn.commit()

            else:
                status = "Not Eligible"

            notifications.append({
                "company": c['name'],
                "status": status
            })

    return render_template('student.html', student=student, notifications=notifications)

# ---------- OFFICER ----------
@app.route('/officer', methods=['GET','POST'])
def officer():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    if request.method == 'POST':
        conn.execute(
            "INSERT INTO students(name,cgpa,skill) VALUES(?,?,?)",
            (request.form['name'], request.form['cgpa'], request.form['skill'])
        )
        conn.commit()

    students = conn.execute("SELECT * FROM students").fetchall()

    return render_template('officer.html', students=students)

# ---------- HR ----------
@app.route('/hr', methods=['GET','POST'])
def hr():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    if request.method == 'POST':
        conn.execute(
            "INSERT INTO companies(name,min_cgpa,skill) VALUES(?,?,?)",
            (request.form['name'], request.form['cgpa'], request.form['skill'])
        )
        conn.commit()

    companies = conn.execute("SELECT * FROM companies").fetchall()

    return render_template('hr.html', companies=companies)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
