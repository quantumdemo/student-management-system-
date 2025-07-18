from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import pandas as pd
import io
from fpdf import FPDF

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        email = request.form["email"]
        password = request.form["password"]

        if role == "admin":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM admin WHERE username = %s", [email])
            user = cur.fetchone()
            cur.close()
            if user and check_password_hash(user[2], password):
                session["user"] = email
                session["role"] = "admin"
                return redirect("/admin")
        elif role == "student":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM student WHERE email = %s", [email])
            student = cur.fetchone()
            cur.close()
            if student and check_password_hash(student[5], password):
                session["user"] = email
                session["role"] = "student"
                return redirect("/student")
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "role" in session and session["role"] == "admin":
        if request.method == "POST":
            file = request.files["excel_file"]
            df = pd.read_excel(file)
            cur = mysql.connection.cursor()
            for _, row in df.iterrows():
                cur.execute("INSERT IGNORE INTO student (full_name, email, class_level, student_id, password_hash) VALUES (%s, %s, %s, %s, %s)",
                    (row["Full Name"], row["Email"], row["Class"], row["Student ID"], generate_password_hash("123456")))
                cur.execute("INSERT INTO result (student_id, subject, score) VALUES (%s, %s, %s)",
                    (row["Student ID"], row["Subject"], row["Score"]))
            mysql.connection.commit()
            cur.close()
            flash("Upload successful.")
        return render_template("admin_dashboard.html")
    return redirect("/")

@app.route("/student")
def student_dashboard():
    if "role" in session and session["role"] == "student":
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM student WHERE email = %s", [session["user"]])
        student = cur.fetchone()
        student_id = student[4]
        cur.execute("SELECT subject, score FROM result WHERE student_id = %s", [student_id])
        results = cur.fetchall()
        cur.close()

        subjects = [r[0] for r in results]
        scores = [r[1] for r in results]
        total = sum(scores)
        avg = total / len(scores) if scores else 0

        def grade(score):
            if score >= 70: return 'A'
            elif score >= 60: return 'B'
            elif score >= 50: return 'C'
            elif score >= 40: return 'D'
            else: return 'F'

        grades = [grade(s) for s in scores]
        comment = "Excellent" if avg >= 70 else "Good" if avg >= 60 else "Fair" if avg >= 50 else "Poor"

        return render_template("student_dashboard.html", name=student[1], class_level=student[3],
                               results=zip(subjects, scores, grades), total=total, average=avg, comment=comment)
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
