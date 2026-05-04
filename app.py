from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cgpa REAL,
        skill TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        min_cgpa REAL,
        skill TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES (?,?,?,?)",
                (name,email,password,role)
            )
            conn.commit()
            return redirect('/login')
        except:
            return "❌ Email already exists"

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email,password)
        ).fetchone()

        if user:
            session['user'] = user['name']
            session['role'] = user['role']

            if user['role'] == "student":
                return redirect('/student')
            elif user['role'] == "officer":
                return redirect('/officer')
            elif user['role'] == "hr":
                return redirect('/hr')
        else:
            return "❌ Invalid login"

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- STUDENT DASHBOARD (WITH NOTIFICATION) ----------------
@app.route('/student')
def student():
    conn = get_db()

    student_name = session.get('user')

    student = conn.execute(
        "SELECT * FROM students WHERE name=?",
        (student_name,)
    ).fetchone()

    companies = conn.execute("SELECT * FROM companies").fetchall()

    notifications = []

    if student:
        for c in companies:
            if student['cgpa'] >= c['min_cgpa'] and c['skill'] in student['skill']:
                notifications.append({
                    "company": c['name'],
                    "status": "Eligible"
                })
            else:
                notifications.append({
                    "company": c['name'],
                    "status": "Not Eligible"
                })

    return render_template(
        'student.html',
        student=student,
        notifications=notifications
    )

# ---------------- OFFICER ----------------
@app.route('/officer', methods=['GET','POST'])
def officer():
    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        cgpa = request.form['cgpa']
        skill = request.form['skill']

        conn.execute(
            "INSERT INTO students(name,cgpa,skill) VALUES (?,?,?)",
            (name,cgpa,skill)
        )
        conn.commit()

    students = conn.execute("SELECT * FROM students").fetchall()
    return render_template('officer.html', students=students)

# ---------------- HR ----------------
@app.route('/hr', methods=['GET','POST'])
def hr():
    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        cgpa = request.form['cgpa']
        skill = request.form['skill']

        conn.execute(
            "INSERT INTO companies(name,min_cgpa,skill) VALUES (?,?,?)",
            (name,cgpa,skill)
        )
        conn.commit()

    companies = conn.execute("SELECT * FROM companies").fetchall()
    return render_template('hr.html', companies=companies)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
