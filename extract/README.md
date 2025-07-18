# Student Management System

This is a web-based Student Management System built with Flask and MySQL.

## Features

- Admin and Student login
- Excel upload for student results
- Automatic calculation of total, average, and grade
- PDF report card generation
- Email notifications on result upload
- Forced password change on first login for students

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/student-management-system.git
   cd student-management-system
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a MySQL database:**
   - Create a database named `studentdb`.
   - Import the `schema.sql` file to create the tables.

5. **Set up environment variables:**
   - Create a `.env` file by copying the `.env.example` file.
   - Update the `.env` file with your database and email credentials.

6. **Run the application:**
   ```bash
   flask run
   ```

## Deployment on Render

1. **Create a new Web Service on Render.**
2. **Connect your GitHub repository.**
3. **Set the following environment variables:**
   - `FLASK_APP=app.py`
   - `FLASK_ENV=production`
   - `SECRET_KEY`
   - `MYSQL_HOST`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DB`
   - `MAIL_SERVER`
   - `MAIL_PORT`
   - `MAIL_USE_TLS`
   - `MAIL_USERNAME`
   - `MAIL_PASSWORD`
4. **Set the start command to:**
   ```bash
   ./start.sh
   ```

## Default Credentials

- **Admin:**
  - **Username:** admin
  - **Password:** admin
- **Student:**
  - **Username:** (from email)
  - **Password:** 123456 (will be forced to change on first login)
