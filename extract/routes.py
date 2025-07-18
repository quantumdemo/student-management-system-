from flask import render_template, redirect, url_for, flash, request, session, send_file
from app import app, mysql, mail
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
import pandas as pd
import io
from fpdf import FPDF

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["role"] = user[3]
            session["first_login"] = user[5]

            if user[3] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                if user[5]: # first_login is True
                    return redirect(url_for("change_password"))
                return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if "role" in session and session["role"] == "admin":
        cur = mysql.connection.cursor()
        cur.execute("SELECT s.full_name, s.student_id, s.class_level, u.username FROM students s JOIN users u ON s.user_id = u.id")
        students = cur.fetchall()
        cur.close()
        return render_template("admin_dashboard.html", students=students)
    return redirect(url_for("login"))

@app.route("/student/dashboard")
def student_dashboard():
    if "role" in session and session["role"] == "student":
        if session.get("first_login"):
            return redirect(url_for("change_password"))

        user_id = session["user_id"]
        cur = mysql.connection.cursor()

        # Get student info
        cur.execute("SELECT * FROM students WHERE user_id = %s", [user_id])
        student = cur.fetchone()
        student_id = student[0]

        # Get results
        cur.execute("""
            SELECT sub.name, r.score
            FROM results r
            JOIN subjects sub ON r.subject_id = sub.id
            WHERE r.student_id = %s
        """, [student_id])
        results = cur.fetchall()
        cur.close()

        total_score = sum(r[1] for r in results)
        average_score = total_score / len(results) if results else 0

        def get_grade(score):
            if score >= 70: return 'A'
            if score >= 60: return 'B'
            if score >= 50: return 'C'
            if score >= 40: return 'D'
            return 'F'

        grades = [(r[0], r[1], get_grade(r[1])) for r in results]

        return render_template("student_dashboard.html", student=student, results=grades, total=total_score, average=average_score)
    return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "role" in session and session["role"] == "student" and session.get("first_login"):
        if request.method == "POST":
            new_password = request.form["new_password"]
            password_hash = generate_password_hash(new_password)
            user_id = session["user_id"]

            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET password_hash = %s, first_login = FALSE WHERE id = %s", (password_hash, user_id))
            mysql.connection.commit()
            cur.close()

            session["first_login"] = False
            flash("Password changed successfully. Please login again.")
            return redirect(url_for("login"))
        return render_template("change_password.html")
    return redirect(url_for("login"))

@app.route("/admin/upload_results", methods=["POST"])
def upload_results():
    if "role" in session and session["role"] == "admin":
        file = request.files["excel_file"]
        df = pd.read_excel(file)
        cur = mysql.connection.cursor()

        for _, row in df.iterrows():
            # Create user for student
            student_username = row["Email"].split('@')[0]
            password_hash = generate_password_hash("123456")
            cur.execute("INSERT IGNORE INTO users (username, password_hash, role) VALUES (%s, %s, 'student')", (student_username, password_hash))
            mysql.connection.commit()

            # Get user_id
            cur.execute("SELECT id FROM users WHERE username = %s", [student_username])
            user_id = cur.fetchone()[0]

            # Create student
            cur.execute("INSERT IGNORE INTO students (user_id, full_name, student_id, class_level) VALUES (%s, %s, %s, %s)",
                        (user_id, row["Full Name"], row["Student ID"], row["Class"]))
            mysql.connection.commit()

            # Get student_id
            cur.execute("SELECT id FROM students WHERE student_id = %s", [row["Student ID"]])
            student_id = cur.fetchone()[0]

            # Insert subjects and results
            for subject in df.columns[4:]:
                cur.execute("INSERT IGNORE INTO subjects (name) VALUES (%s)", [subject])
                mysql.connection.commit()
                cur.execute("SELECT id FROM subjects WHERE name = %s", [subject])
                subject_id = cur.fetchone()[0]

                cur.execute("INSERT INTO results (student_id, subject_id, score, term, session) VALUES (%s, %s, %s, %s, %s)",
                            (student_id, subject_id, row[subject], "First", "2023/2024"))
                mysql.connection.commit()

            # Send email
            msg = Message('Results Uploaded', sender = app.config['MAIL_USERNAME'], recipients = [row["Email"]])
            msg.body = f"Dear {row['Full Name']},\n\nYour results have been uploaded. Please login to view them.\n\nThank you."
            mail.send(msg)

        cur.close()
        flash("Results uploaded and emails sent successfully.")
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))

@app.route('/student/report/download')
def download_report():
    if "role" in session and session["role"] == "student":
        user_id = session["user_id"]
        cur = mysql.connection.cursor()

        # Get student info
        cur.execute("SELECT * FROM students WHERE user_id = %s", [user_id])
        student = cur.fetchone()
        student_id = student[0]

        # Get results
        cur.execute("""
            SELECT sub.name, r.score
            FROM results r
            JOIN subjects sub ON r.subject_id = sub.id
            WHERE r.student_id = %s
        """, [student_id])
        results = cur.fetchall()
        cur.close()

        total_score = sum(r[1] for r in results)
        average_score = total_score / len(results) if results else 0

        def get_grade(score):
            if score >= 70: return 'A'
            if score >= 60: return 'B'
            if score >= 50: return 'C'
            if score >= 40: return 'D'
            return 'F'

        grades = [(r[0], r[1], get_grade(r[1])) for r in results]

        # PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Report Card", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Name: {student[2]}", ln=True)
        pdf.cell(200, 10, txt=f"Student ID: {student[3]}", ln=True)
        pdf.cell(200, 10, txt=f"Class: {student[4]}", ln=True)

        for subject, score, grade in grades:
            pdf.cell(100, 10, txt=subject, border=1)
            pdf.cell(50, 10, txt=str(score), border=1)
            pdf.cell(50, 10, txt=grade, border=1, ln=True)

        pdf.cell(200, 10, txt=f"Total Score: {total_score}", ln=True)
        pdf.cell(200, 10, txt=f"Average Score: {average_score}", ln=True)

        # Create a temporary file in memory
        pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin-1'))

        return send_file(pdf_output, as_attachment=True, download_name=f'report_card_{student[3]}.pdf', mimetype='application/pdf')
    return redirect(url_for("login"))
