import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import csv
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from tkinter import filedialog
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from plyer import notification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from tkinter import simpledialog
import tkinter as tk
from PIL import Image, ImageTk


# Initialize the tasks dictionary
tasks = {}

# Global variable for the logged-in user
current_user = ""

# File to store users' credentials
USER_FILE = "users.csv"
TASK_FILE = "tasks.csv"  # Shared task file for all users

cred = credentials.Certificate("calendar-395f6-firebase-adminsdk-fbsvc-37a953df77.json")
default_app = firebase_admin.initialize_app(cred, {
'databaseURL': 'https://calendar-395f6-default-rtdb.firebaseio.com/'
})

ref = db.reference("/User")
ref2 = db.reference("/Task")




# Login Window Function
def login_window():
    def authenticate():
        global current_user
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
           user_ref = ref.child(username).get()

           if user_ref is not None and user_ref.get('password') == password:
               current_user = username
               login_window_instance.destroy()
               root.deiconify()
               user_label.config(text=f"Logged in as : {current_user}")
               load_tasks_from_firebase()

           else:
               messagebox.showerror("Login failed", "Invalid username and password")
        else: 
            messagebox.showerror("Input Error", "Please enter both username and password!")

    def show_register_window():
        login_window_instance.destroy()
        register_window()

    login_window_instance = tk.Toplevel()
    login_window_instance.title("Login")
    login_window_instance.geometry("600x400")
    login_window_instance.resizable(False, False)
    login_window_instance.configure(bg="#1E1E2E")
    
    image = Image.open("logo.png")  # Replace with your image path
    image = image.resize((250, 120))  # Resize for better UI balance
    photo = ImageTk.PhotoImage(image)
    login_window_instance.image = photo  # Prevent garbage collection

    # Keep a reference to avoid garbage collection
    image_label = tk.Label(login_window_instance, image=photo, bg="#1E1E2E")
    image_label.pack(pady=(20, 10))  # Space above and below image
    
    label = ttk.Label(login_window_instance, text="Login", font=("Segoe UI", 16, "bold"), background="#1E1E2E", foreground="white")
    label.pack(pady=(0, 10))
    
    username_label = ttk.Label(login_window_instance, text="Username:")
    username_label.pack()
    username_entry = ttk.Entry(login_window_instance)
    username_entry.pack(pady=5)
    
    password_label = ttk.Label(login_window_instance, text="Password:")
    password_label.pack()
    password_entry = ttk.Entry(login_window_instance, show="*")
    password_entry.pack(pady=5)
    
    login_button = ttk.Button(login_window_instance, text="Login", command=authenticate)
    login_button.pack(pady=(10, 5))
    
    register_button = ttk.Button(login_window_instance, text="Register", command=show_register_window)
    register_button.pack()
    
    login_window_instance.update_idletasks()
    window_width = 600
    window_height = 400
    screen_width = login_window_instance.winfo_screenwidth()
    screen_height = login_window_instance.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    login_window_instance.geometry(f"{window_width}x{window_height}+{x}+{y}")

    login_window_instance.mainloop()

def register_window():
    def register_user():
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            if ref.child(username).get() is not None:
                messagebox.showerror("Registration Failed", "Username already exists!")
                return
            
            ref.child(username).set({
                'username': username,
                'password': password
            })

                

            messagebox.showinfo("Success", "You have successfully registered!")
            register_window_instance.destroy()
            login_window()
        else:
            messagebox.showerror("Input Error", "Please enter both username and password!")

    register_window_instance = tk.Toplevel()
    register_window_instance.title("Register")
    register_window_instance.geometry("600x400")
    register_window_instance.resizable(False, False)
    register_window_instance.configure(bg="#1E1E2E")

    # Load and display the image
    image = Image.open("logo.png")  # Replace with your image path
    image = image.resize((250, 120))  # Resize as needed
    photo = ImageTk.PhotoImage(image)
    register_window_instance.image = photo  # Prevent garbage collection

    image_label = tk.Label(register_window_instance, image=photo, bg="#1E1E2E")
    image_label.pack(pady=(20, 10))

    # Title
    label = ttk.Label(register_window_instance, text="Create Account", font=("Segoe UI", 16, "bold"), background="#1E1E2E", foreground="white")
    label.pack(pady=(0, 10))

    # Username input
    username_label = ttk.Label(register_window_instance, text="Username:")
    username_label.pack()
    username_entry = ttk.Entry(register_window_instance)
    username_entry.pack(pady=5)

    # Password input
    password_label = ttk.Label(register_window_instance, text="Password:")
    password_label.pack()
    password_entry = ttk.Entry(register_window_instance, show="*")
    password_entry.pack(pady=5)

    # Register button
    register_button = ttk.Button(register_window_instance, text="Register", command=register_user)
    register_button.pack(pady=10)

    # Center the window
    register_window_instance.update_idletasks()
    window_width = 600
    window_height = 400
    screen_width = register_window_instance.winfo_screenwidth()
    screen_height = register_window_instance.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    register_window_instance.geometry(f"{window_width}x{window_height}+{x}+{y}")

    register_window_instance.mainloop()

def get_task_file():
    return TASK_FILE  # Shared task file for all users

def save_tasks_to_csv():
    with open(get_task_file(), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Task", "Employee", "Status"])
        for date_obj, task_list in tasks.items():
            for task, employee, status in task_list:
                writer.writerow([date_obj.strftime("%m/%d/%y"), task, employee, status])



from plyer import notification

def load_tasks_from_firebase():
    task_treeview.delete(*task_treeview.get_children())  # Clear existing tasks
    tasks.clear()  # Clear the tasks before reloading

    try:
        tasks_ref = db.reference("/Task")
        task_data = tasks_ref.get()  # Retrieve all tasks from Firebase

        print("Fetched task_data:", task_data)  # Debug print to check the data structure

        if task_data:
            for date_str, date_tasks in task_data.items():
                if isinstance(date_tasks, dict):  # ✅ safeguard level 1
                    for employee, employee_tasks in date_tasks.items():
                        if isinstance(employee_tasks, dict):  # ✅ safeguard level 2
                            for task_id, task_info in employee_tasks.items():
                                if isinstance(task_info, dict):  # ✅ safeguard level 3
                                    task = task_info.get('task')
                                    status = task_info.get('status', "Upcoming")
                                    start_time = task_info.get('start_time')
                                    end_time = task_info.get('end_time')

                                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                                    tasks.setdefault(date_obj, []).append((task, employee, status))

                                    if status != "Removed":
                                        task_treeview.insert(
                                            "", "end",
                                            values=(date_obj.strftime("%b/%d/%y"), task, employee, status)
                                        )

            # Trigger a notification to all users on task update
            notification.notify(
                title="Task Update",
                message="A task has been added or updated in the system!",
                timeout=10
            )
            highlight_dates()  # Update date highlights on the calendar
    except Exception as e:
        print(f"Error loading tasks from Firebase: {e}")



def highlight_dates():
    cal.calevent_remove('all')  # Clear previous highlights

    for date_obj, task_list in tasks.items():
        statuses = {status for _, _, status in task_list}
        if "Ongoing" in statuses:
            cal.calevent_create(date_obj, "Ongoing Task", "ongoing")
        elif "Upcoming" in statuses:
            cal.calevent_create(date_obj, "Upcoming Task", "upcoming")
        elif "Done" in statuses:
            cal.calevent_create(date_obj, "Done Task", "done")

    # Apply tag colors
    cal.tag_config("ongoing", background="orange", foreground="black")
    cal.tag_config("upcoming", background="lightblue", foreground="black")
    cal.tag_config("done", background="lightgreen", foreground="black")


def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y").date()
    except ValueError:
        messagebox.showerror("Date Format Error", f"Invalid date format: {date_str}")
        return

    employee = current_user

    start_time = start_hour.get()
    end_time = end_hour.get()
    task_with_time = f"{task} ({start_time} - {end_time})"

    if task:
        if date_obj > datetime.today().date():
            status = "Upcoming"
        elif date_obj == datetime.today().date():
            status = "Ongoing"
        else:
            status = "Done"

        task_data = {
            'task': task_with_time,
            'employee': employee,
            'status': status,
            'start_time': start_time,
            'end_time': end_time
        }

        # Add the task to Firebase under the correct date and employee
        task_ref = ref2.child(date_obj.strftime('%Y-%m-%d')).child(employee)
        task_ref.push(task_data)

        # Update local tasks dictionary to reflect changes
        tasks.setdefault(date_obj, []).append((task_with_time, employee, status))

        # Add task to Treeview for immediate display
        task_treeview.insert("", "end", values=(date_obj.strftime("%b/%d/%y"), task_with_time, employee, status))
        
        # Clear the task input field
        task_entry.delete(0, tk.END)

        # Update the calendar view and save tasks to CSV
        notification.notify(
            title="📝 Task Added",
            message=f"{task_with_time} on {date_obj.strftime('%b %d, %Y')}",
            timeout=5
        )

        # Update the calendar view and save tasks to CSV
        highlight_dates()
        save_tasks_to_csv()

        # Force reload of tasks from Firebase to synchronize the Treeview with the database
        messagebox.showinfo("Task Added", f"Task added successfully:\n\nTask: {task_with_time}\nDate: {date_obj.strftime('%b %d, %Y')}")

        load_tasks_from_firebase()

    else:
        messagebox.showwarning("Warning", "Task must be filled!")

def listen_for_changes():
    def notify_all_users(event):
        if event.event_type == 'put' and event.data and isinstance(event.data, dict):
            path_parts = event.path.strip("/").split("/")
            if len(path_parts) == 3:  # format: /YYYY-MM-DD/username/task_id
                task_data = event.data
                task = task_data.get("task", "Unknown Task")
                employee = task_data.get("employee", "Someone")
                date_str = path_parts[0]
                notification.notify(
                    title="📢 New Task Added",
                    message=f"{employee} added: {task} on {date_str}",
                    timeout=5  # seconds
                )
                load_tasks_from_firebase()  # Optional: refresh view

    ref2.listen(notify_all_users)


def remove_task():
    selected_item = task_treeview.selection()
    if selected_item:
        item_values = task_treeview.item(selected_item, "values")
        if item_values:
            date_str, task, employee, status = item_values
            date_obj = datetime.strptime(date_str, "%b/%d/%y").date()

            # Update tasks locally
            if date_obj in tasks:
                tasks[date_obj] = [
                    (t, e, "Removed") if (t == task and e == employee) else (t, e, s)
                    for (t, e, s) in tasks[date_obj]
                ]
            
            # Update the task in Firebase
            task_ref = ref2.child(date_obj.strftime('%Y-%m-%d')).child(employee)
            for task_id, task_info in task_ref.get().items():
                if task_info.get('task') == task:
                    task_ref.child(task_id).update({'status': 'Removed'})
                    break
            
            # Remove the task from the Treeview
            task_treeview.delete(selected_item)
            highlight_dates()
            save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "No task selected!")

def mark_task_as_done():
    selected_item = task_treeview.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No task selected!")
        return

    try:
        item_values = task_treeview.item(selected_item, "values")
        if not item_values:
            messagebox.showerror("Error", "Unable to retrieve task information.")
            return

        date_str, task, employee, current_status = item_values
        if current_status == "Done":
            messagebox.showinfo("Already Done", "This task is already marked as done.")
            return

        confirm = messagebox.askyesno("Mark as Done", f"Are you sure you want to mark this task as done?\n\nTask: {task}")
        if not confirm:
            return

        date_obj = datetime.strptime(date_str, "%b/%d/%y").date()

        # Update tasks locally
        if date_obj in tasks:
            tasks[date_obj] = [
                (t, e, "Done") if (t == task and e == employee) else (t, e, s)
                for (t, e, s) in tasks[date_obj]
            ]

        # Update the task in Firebase
        task_ref = ref2.child(date_obj.strftime('%Y-%m-%d')).child(employee)
        for task_id, task_info in task_ref.get().items():
            if task_info.get('task') == task:
                task_ref.child(task_id).update({'status': 'Done'})
                break

        # Update the Treeview
        task_treeview.item(selected_item, values=(date_str, task, employee, "Done"))
        highlight_dates()
        save_tasks_to_csv()

    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")



def logout():
    global current_user
    current_user = ""
    root.withdraw()
    login_window()

def sort_by_month():
    sorted_tasks = sorted(tasks.items(), key=lambda x: x[0].month)
    task_treeview.delete(*task_treeview.get_children())  # Clear current Treeview

    # Reload tasks in sorted order
    for date_obj, task_list in sorted_tasks:
        for task, employee, status in task_list:
            if status != "Removed":
                task_treeview.insert("", "end", values=(date_obj.strftime("%b/%d/%y"), task, employee, status))

def export_to_pdf():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF"
    )
    if not file_path:
        return  # User cancelled

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, height - 50, f"Task List for {current_user}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, height - 80, "Date")
    c.drawString(130, height - 80, "Task")
    c.drawString(330, height - 80, "User")
    c.drawString(430, height - 80, "Status")

    y = height - 100
    c.setFont("Helvetica", 10)
    for item in task_treeview.get_children():
        values = task_treeview.item(item, "values")
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(30, y, values[0])
        c.drawString(130, y, values[1])
        c.drawString(330, y, values[2])
        c.drawString(430, y, values[3])
        y -= 20

    c.save()
    messagebox.showinfo("Exported", f"Tasks successfully exported to {file_path}")


def export_selected_task_as_letter():
    selected_item = task_treeview.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No task selected!")
        return

    item_values = task_treeview.item(selected_item, "values")
    if not item_values:
        messagebox.showerror("Error", "Unable to retrieve task information.")
        return

    date_str, task, employee, status = item_values

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Export Task as Letter"
    )

    if not file_path:
        return  # User cancelled

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Task Assignment Letter")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 140, f"Date Assigned: {date_str}")
    c.drawString(50, height - 160, f"Assigned To: {employee}")
    c.drawString(50, height - 180, f"Task: {task}")
    c.drawString(50, height - 200, f"Status: {status}")
    
    c.drawString(50, height - 240, "Dear Ma'am/Sir,")
    c.drawString(50, height - 260, f"You have been assigned the following task:")
    c.drawString(70, height - 280, f"• {task}")
    c.drawString(50, height - 300, "Please make sure to complete this task as scheduled.")
    c.drawString(50, height - 340, "Sincerely,")
    c.drawString(50, height - 360, f"{current_user}")

    c.save()
    messagebox.showinfo("Exported", f"Letter successfully exported to {file_path}")

def send_task_email():
    selected_item = task_treeview.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No task selected!")
        return

    item_values = task_treeview.item(selected_item, "values")
    if not item_values:
        messagebox.showerror("Error", "Unable to retrieve task information.")
        return

    date_str, task, employee, status = item_values

    # Ask for the recipient email address (the connected user's email)
    recipient_email = simpledialog.askstring("Email", "Enter your email address:")
    if not recipient_email:
        messagebox.showerror("Error", "No email address entered.")
        return

    # Email content with improved subject and body
    subject = f"Task Assigned: {task} for {employee} – {date_str}"
    body = f"""
    Hello,

    This is a reminder about a task assigned to you:

    Task: {task}
    Assigned to: {employee}
    Due Date: {date_str}
    Status: {status}

    Please take the necessary actions for this task at your earliest convenience.

    If you have any questions or need further details, feel free to reach out.

    Best regards,
    Your Name
    Your Job Title or Company Name
    """

    # SMTP server configuration
    smtp_server = "smtp.gmail.com"  
    smtp_port = 587  
    sender_email = "reminderco05@gmail.com"  
    sender_password = "wtxt djzs igiw fkis"  # Use an App Password for Gmail

    try:
        # Set up the server and login
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(sender_email, sender_password)

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Attach the email body
        msg.attach(MIMEText(body, "plain"))

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        messagebox.showinfo("Success", "Email sent successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while sending the email: {e}")


root = tk.Tk()
root.title("To-Do Calendar")
root.geometry("1050x680")
root.configure(bg="#1E1E2E")
root.withdraw()

# Style Setup
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#1E1E2E", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", background="#4C566A", foreground="white", font=("Segoe UI", 10), padding=5)
style.map("TButton", background=[("active", "#5E81AC")])
style.configure("TCombobox", fieldbackground="#3B4252", background="#3B4252", foreground="white")
style.configure("Treeview", background="#2E3440", fieldbackground="#2E3440", foreground="white", font=("Segoe UI", 10))
style.configure("Treeview.Heading", background="#4C566A", foreground="white", font=("Segoe UI", 10, "bold"))

user_label = ttk.Label(root, text="")
user_label.pack(anchor="w", padx=10, pady=(10, 0))

logout_button = ttk.Button(root, text="🔒 Logout", command=logout)
logout_button.pack(anchor="w", padx=10, pady=(0, 10))

# Export Buttons
export_buttons_frame = ttk.Frame(root)
export_buttons_frame.pack(anchor="w", padx=10, pady=(0, 10))

export_button = ttk.Button(export_buttons_frame, text="📄 Export to PDF", command=export_to_pdf)
export_button.pack(side="left", padx=(0, 5))

export_letter_button = ttk.Button(export_buttons_frame, text="✉ Export as Letter", command=export_selected_task_as_letter)
export_letter_button.pack(side="left", padx=5)

send_email_button = ttk.Button(export_buttons_frame, text="📧 Send to Email", command=send_task_email)
send_email_button.pack(side="left")

# Main Layout
main_frame = tk.Frame(root, bg="#1E1E2E")
main_frame.pack(expand=True, fill="both", padx=10, pady=10)

# Calendar Section
calendar_frame = tk.Frame(main_frame, bg="#1E1E2E")
calendar_frame.pack(side="left", fill="both", expand=True)

cal = Calendar(calendar_frame, selectmode='day',
               background="#3B4252", foreground="white",
               selectbackground="#5E81AC", headersbackground="#2E3440",
               font=("Segoe UI", 12), date_pattern="mm/dd/yyyy",
               cursor="hand2", borderwidth=2)
cal.pack(padx=5, pady=5, expand=True, fill="both")
calendar_frame.config(width=500, height=700)
calendar_frame.pack_propagate(False)

# Task Section
task_frame = tk.Frame(main_frame, bg="#1E1E2E")
task_frame.pack(side="right", fill="both", expand=False, padx=10)

# Task Input Row
input_row = tk.Frame(task_frame, bg="#1E1E2E")
input_row.pack(pady=(0, 10), fill="x")

task_entry = ttk.Entry(input_row, font=("Segoe UI", 10), width=40)
task_entry.pack(side="left", padx=(0, 10))

hour_values = [f"{h}:00 {'AM' if h < 12 else 'PM'}" for h in range(1, 13)]

ttk.Label(input_row, text="Start:", background="#1E1E2E", foreground="white").pack(side="left")
start_hour = ttk.Combobox(input_row, values=hour_values, width=10)
start_hour.pack(side="left", padx=(5, 10))
start_hour.set("6:00 AM")

ttk.Label(input_row, text="End:", background="#1E1E2E", foreground="white").pack(side="left")
end_hour = ttk.Combobox(input_row, values=hour_values, width=10)
end_hour.pack(side="left", padx=(5, 0))
end_hour.set("6:00 PM")

# Buttons
for btn_text, cmd in [
    ("✔ Add Task", add_task),
    ("✖ Remove Task", remove_task),
    ("👍🏻 Mark as Done", mark_task_as_done),
    ("🔢 Sort by Month", sort_by_month)
]:
    ttk.Button(task_frame, text=btn_text, command=cmd).pack(pady=3, fill="x")

# Treeview
task_treeview = ttk.Treeview(
    task_frame,
    columns=("📅 Date", "📝 Task", "👨🏻‍💻 Employee", "📶 Status"),
    show="headings",
    height=10
)
task_treeview.pack(expand=False, fill="both", pady=(10, 0))

# Set column widths
task_treeview.column("📅 Date", width=100, anchor="center")
task_treeview.column("📝 Task", width=250, anchor="w")
task_treeview.column("👨🏻‍💻 Employee", width=150, anchor="center")
task_treeview.column("📶 Status", width=100, anchor="center")

for col in task_treeview["columns"]:
    task_treeview.heading(col, text=col)


TASK_COLORS = {
    "Upcoming": "#D08770",
    "Ongoing": "#A3BE8C",
    "Done": "#B48EAD",
    "Removed": "#E5E9F0"
}

def listen_for_changes():
    ref2.listen(lambda event: load_tasks_from_firebase())

# Call this function when the app starts
listen_for_changes()


login_window()
root.mainloop()
