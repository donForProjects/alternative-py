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
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import qrcode
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

main = Blueprint('main', __name__)

USER_FILE = 'users.csv'
TASK_FILE = 'tasks.csv'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not firebase_admin._apps:
    cred = credentials.Certificate('app\calendar-395f6-firebase-adminsdk-fbsvc-ca07c66d17.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://calendar-395f6-default-rtdb.firebaseio.com/'
    })

# User routes
@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Please enter both username and password!')
            return redirect(url_for('main.login'))

        users_ref = db.reference('User')
        user_data = users_ref.child(username).get()

        if user_data:
            stored_hash = user_data.get('password')
            if stored_hash and check_password_hash(stored_hash, password):
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

        if not username or not password:
            flash('Please enter both username and password!')
            return redirect(url_for('main.register'))

        users_ref = db.reference('User')

        # Check if user already exists
        if users_ref.child(username).get() is not None:
            flash('Username already exists!')
            return redirect(url_for('main.register'))

        # Save new user with hashed password
        users_ref.child(username).set({
            'username': username,
            'password': generate_password_hash(password)
        })

        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

# Dashboard and Task Management
@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user = session['user']
    
    # Handle task submission
    if request.method == 'POST':
        task = request.form['task']
        date = request.form['date']
        start_time = request.form['start']
        end_time = request.form['end']

        status = "Upcoming" if datetime.strptime(date, "%Y-%m-%d").date() > datetime.today().date() else "Ongoing"

        # Generate a unique task ID using datetime
        task_id = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        task_ref = db.reference(f"/Task/{date}/{user}/{task_id}")
        task_ref.set({
            'task': task,
            'start_time': start_time,
            'end_time': end_time,
            'status': status
        })

        flash('Task added successfully!')

    # Fetch tasks for the current user
    tasks = []
    try:
        tasks_ref = db.reference("/Task")
        all_tasks = tasks_ref.get()

        if all_tasks:
            for date_str, date_tasks in all_tasks.items():
                if user in date_tasks:
                    user_tasks = date_tasks[user]
                    for task_id, task_info in user_tasks.items():
                        task = task_info.get('task')
                        status = task_info.get('status', 'Upcoming')
                        start_time = task_info.get('start_time')
                        end_time = task_info.get('end_time')

                        tasks.append([
                            user,
                            date_str,
                            f"{task} ({start_time} - {end_time})",
                            status
                        ])
    except Exception as e:
        flash(f"Error loading tasks: {e}")

    # Load image filenames from uploads folder
    image_folder = os.path.join('static', 'uploads')
    image_files = set(os.listdir(image_folder)) if os.path.exists(image_folder) else set()

    return render_template(
        'dashboard.html',
        user=user,
        tasks=tasks,
        enumerate=enumerate,
        image_files=image_files
    )

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

# Delete Task
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# Upload Task Image
@main.route('/upload_picture', methods=['POST'])
def upload_picture():
    task_index = int(request.form['task_index'])
    picture = request.files['picture']

    if picture and allowed_file(picture.filename):
        try:
            filename = secure_filename(picture.filename)
            filename = f"task_{task_index}_{filename}"

            # Normalize the path with forward slashes
            relative_path = os.path.join('uploads', filename).replace('\\', '/')
            absolute_path = os.path.join('static', relative_path)

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            print(f"Saving to: {absolute_path}")
            picture.save(absolute_path)

            with open(TASK_FILE, 'r') as f:
                tasks = list(csv.reader(f))

            if 0 <= task_index < len(tasks):
                if len(tasks[task_index]) < 5:
                    tasks[task_index].append(relative_path)
                else:
                    tasks[task_index][4] = relative_path

                with open(TASK_FILE, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(tasks)

                print("THIS WORKS")
                print("it saves")
                flash("Picture uploaded successfully!")
            else:
                flash("Invalid task index.")
        except Exception as e:
            flash(f"Error uploading picture: {str(e)}")
    else:
        flash("No file selected or invalid file type.")

    return redirect(url_for('main.dashboard'))

# Export Tasks to PDF
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

# Send Task Details via Email
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

def generate_qr_code(task_url):
    base_url = request.host_url  # Get the host URL (e.g., http://localhost:5000/)
    full_url = base_url + task_url  # Combine the base URL with the relative URL

    qr = qrcode.make(full_url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@main.route('/generate_qr/<int:task_index>', methods=['GET'])
def generate_qr(task_index):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    tasks = []
    try:
        with open(TASK_FILE, 'r') as csvfile:
            reader = csv.reader(csvfile)
            tasks = [row for row in reader if row[0] == session['user']]
    except FileNotFoundError:
        tasks = []

    if task_index >= len(tasks):
        flash("Task not found!")
        return redirect(url_for('main.dashboard'))

    task = tasks[task_index]

    # Generate a URL for the task details page
    task_url = url_for('main.task_details', task_index=task_index, _external=True)

    # Generate the QR code for the task details URL
    qr_code_image = generate_qr_code(task_url)

    # Return the QR code as an image
    return send_file(qr_code_image, mimetype='image/png', as_attachment=True, download_name=f'task_{task_index}_qr.png')

@main.route('/task_details/<int:task_index>')
def task_details(task_index):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    tasks = []
    try:
        with open(TASK_FILE, 'r') as csvfile:
            reader = csv.reader(csvfile)
            tasks = [row for row in reader if row[0] == session['user']]
    except FileNotFoundError:
        tasks = []

    if task_index >= len(tasks):
        flash("Task not found!")
        return redirect(url_for('main.dashboard'))

    task = tasks[task_index]

    return render_template('task_details.html', task=task)
