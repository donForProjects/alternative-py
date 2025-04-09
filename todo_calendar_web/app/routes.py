from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import csv
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

main = Blueprint('main', __name__)

USER_FILE = 'users.csv'
TASK_FILE = 'tasks.csv'

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if os.path.exists(USER_FILE):
            with open(USER_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['username'] == username and row['password'] == password:
                        session['user'] = username
                        return redirect(url_for('main.dashboard'))
        flash('Invalid credentials')

    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.login'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if os.path.exists(USER_FILE):
            with open(USER_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['username'] == username:
                        flash('Username already exists')
                        return redirect(url_for('main.register'))

        write_header = not os.path.exists(USER_FILE)
        with open(USER_FILE, 'a', newline='') as csvfile:
            fieldnames = ['username', 'password']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow({'username': username, 'password': password})

        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        task = request.form['task']
        date = request.form['date']
        start_time = request.form['start']
        end_time = request.form['end']
        user = session['user']
        status = "Upcoming" if datetime.strptime(date, "%Y-%m-%d").date() > datetime.today().date() else "Ongoing"

        with open(TASK_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([user, date, f"{task} ({start_time} - {end_time})", status])

        flash('Task added successfully!')

    tasks = []
    try:
        with open(TASK_FILE, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == session['user']:  # Assuming the user is stored in the first column
                    tasks.append(row)
    except FileNotFoundError:
        tasks = []

    return render_template('dashboard.html', user=session['user'], tasks=tasks, enumerate=enumerate)


@main.route('/mark_as_done/<task_index>', methods=['GET'])
def mark_as_done(task_index):
    try:
        task_index = int(task_index)  # Try to convert to an integer
    except ValueError:
        flash("Invalid task index")
        return redirect(url_for('main.dashboard'))

    # Proceed to read the tasks from the CSV file
    tasks = []
    try:
        with open(TASK_FILE, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                tasks.append(row)
    except FileNotFoundError:
        tasks = []

    # Check if the task index is valid
    if 0 <= task_index < len(tasks):
        tasks[task_index][3] = "Done"  # Assuming the status is at index 3
        try:
            with open(TASK_FILE, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(tasks)

            flash('Task marked as done!')
        except Exception as e:
            flash(f"Error updating task: {str(e)}")
    else:
        flash('Task not found!')

    return redirect(url_for('main.dashboard'))



@main.route('/delete_task/<int:task_index>')
def delete_task(task_index):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    updated = []
    with open(TASK_FILE, newline='') as csvfile:
        reader = list(csv.reader(csvfile))
        count = -1
        for row in reader:
            if row and row[0] == session['user']:
                count += 1
                if count == task_index:
                    continue
            updated.append(row)

    with open(TASK_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(updated)

    flash("Task deleted!")
    return redirect(url_for('main.dashboard'))

@main.route('/export_pdf')
def export_pdf():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Task List for {session['user']}")
    y -= 30
    p.setFont("Helvetica", 10)

    with open(TASK_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0] == session['user']:
                line = f"Date: {row[1]} | Task: {row[2]} | Status: {row[3]}"
                p.drawString(50, y, line)
                y -= 20
                if y < 50:
                    p.showPage()
                    y = height - 50

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='tasks.pdf', mimetype='application/pdf')

@main.route('/send_email/<int:task_index>')
def send_email(task_index):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_tasks = []
    with open(TASK_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0] == session['user']:
                user_tasks.append(row)

    if task_index >= len(user_tasks):
        flash('Invalid task index.')
        return redirect(url_for('main.dashboard'))

    task = user_tasks[task_index]
    to_email = "youremail@example.com"  # Replace with actual recipient
    subject = f"Task Notification: {task[2]}"
    body = f"Date: {task[1]}\nTask: {task[2]}\nStatus: {task[3]}"

    msg = MIMEMultipart()
    msg['From'] = "reminderco05@gmail.com"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(msg['From'], "wtxt djzs igiw fkis")  # Use app-specific password
        server.send_message(msg)
        server.quit()
        flash('Email sent successfully!')
    except Exception as e:
        flash(f'Email failed: {e}')

    return redirect(url_for('main.dashboard'))
