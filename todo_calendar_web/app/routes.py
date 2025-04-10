from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import qrcode
import firebase_admin
from firebase_admin import credentials, db

main = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not firebase_admin._apps:
    cred = credentials.Certificate('app/calendar-395f6-firebase-adminsdk-fbsvc-751e85c186.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://calendar-395f6-default-rtdb.firebaseio.com/'
    })

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users_ref = db.reference('User')
        user_data = users_ref.child(username).get()

        if user_data and user_data.get('password') == password:
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

        users_ref = db.reference('User')

        if users_ref.child(username).get() is not None:
            flash('Username already exists!')
            return redirect(url_for('main.register'))

        users_ref.child(username).set({
            'username': username,
            'password': password
        })

        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']

    if request.method == 'POST':
        task = request.form['task']
        date = request.form['date']
        start_time = request.form['start']
        end_time = request.form['end']

        status = "Upcoming" if datetime.strptime(date, "%Y-%m-%d").date() > datetime.today().date() else "Ongoing"
        task_id = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        db.reference(f"/Task/{date}/{user}/{task_id}").set({
            'task': task,
            'start_time': start_time,
            'end_time': end_time,
            'status': status
        })

        flash('Task added successfully!')

    tasks = []
    try:
        all_tasks = db.reference("/Task").get()
        if all_tasks:
            for date_str, date_tasks in all_tasks.items():
                if user in date_tasks:
                    for task_id, task_info in date_tasks[user].items():
                        tasks.append([
                            date_str,
                            f"{task_info.get('task')} ({task_info.get('start_time')} - {task_info.get('end_time')})",
                            task_info.get('image'),
                            task_info.get('status', 'Upcoming'),
                            task_id
                        ])
    except Exception as e:
        flash(f"Error loading tasks: {e}")

    return render_template("dashboard.html", user=user, tasks=tasks)

@main.route('/mark_as_done/<task_id>/<date>', methods=['GET'])
def mark_as_done(task_id, date):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    task_ref = db.reference(f"/Task/{date}/{user}/{task_id}")
    if task_ref.get():
        task_ref.update({'status': 'Done'})
        flash("Task marked as done!")
    else:
        flash("Task not found.")

    return redirect(url_for('main.dashboard'))

@main.route('/delete_task/<task_id>/<date>')
def delete_task(task_id, date):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    db.reference(f"/Task/{date}/{user}/{task_id}").delete()
    flash("Task deleted!")
    return redirect(url_for('main.dashboard'))

@main.route('/upload_picture', methods=['POST'])
def upload_picture():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    picture = request.files['picture']
    task_id = request.form['task_id']
    date = request.form['date']
    user = session['user']

    if picture and allowed_file(picture.filename):
        filename = secure_filename(picture.filename)
        relative_path = os.path.join('uploads', f"task_{task_id}_{filename}").replace('\\', '/')
        absolute_path = os.path.join('static', relative_path)
        picture.save(absolute_path)

        db.reference(f"/Task/{date}/{user}/{task_id}/image").set(relative_path)
        flash("Picture uploaded and linked successfully!")
    else:
        flash("Invalid file or no file selected.")

    return redirect(url_for('main.dashboard'))

@main.route('/send_email/<task_id>/<date>')
def send_email(task_id, date):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    task_data = db.reference(f"/Task/{date}/{user}/{task_id}").get()

    if not task_data:
        flash("Task not found.")
        return redirect(url_for('main.dashboard'))

    to_email = "m.cleighronne@gmail.com"
    subject = f"Task Notification: {task_data.get('task')}"
    body = (
        f"Date: {date}\n"
        f"Task: {task_data.get('task')}\n"
        f"Start: {task_data.get('start_time')}\n"
        f"End: {task_data.get('end_time')}\n"
        f"Status: {task_data.get('status')}"
    )

    msg = MIMEMultipart()
    msg['From'] = "reminderco05@gmail.com"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(msg['From'], "wtxt djzs igiw fkis")
        server.send_message(msg)
        server.quit()
        flash('Email sent successfully!')
    except Exception as e:
        flash(f'Email failed: {e}')

    return redirect(url_for('main.dashboard'))

@main.route('/export_pdf')
def export_pdf():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Task List for {user}")
    y -= 30
    p.setFont("Helvetica", 10)

    try:
        tasks_ref = db.reference("/Task")
        all_tasks = tasks_ref.get()

        if all_tasks:
            for date, date_tasks in all_tasks.items():
                if user in date_tasks:
                    for task_id, task_data in date_tasks[user].items():
                        line = (
                            f"Date: {date} | Task: {task_data.get('task')} "
                            f"({task_data.get('start_time')} - {task_data.get('end_time')}) | "
                            f"Status: {task_data.get('status')}"
                        )
                        p.drawString(50, y, line)
                        y -= 20
                        if y < 50:
                            p.showPage()
                            y = height - 50

        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='tasks.pdf', mimetype='application/pdf')

    except Exception as e:
        flash(f"Failed to export tasks: {e}")
        return redirect(url_for('main.dashboard'))

@main.route('/generate_qr/<task_id>/<date>')
def generate_qr(task_id, date):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    task_url = url_for('main.task_details', task_id=task_id, date=date)
    qr_image = generate_qr_code(task_url)

    return send_file(qr_image, mimetype='image/png', as_attachment=True, download_name=f'task_{task_id}_qr.png')

@main.route('/task_details/<task_id>/<date>')
def task_details(task_id, date):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    task = db.reference(f"/Task/{date}/{user}/{task_id}").get()

    if not task:
        flash("Task not found!")
        return redirect(url_for('main.dashboard'))

    return render_template('task_details.html', task=task)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_qr_code(task_url):
    base_url = request.host_url
    full_url = base_url + task_url.lstrip('/')
    qr = qrcode.make(full_url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io
