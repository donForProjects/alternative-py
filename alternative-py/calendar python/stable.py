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

# Initialize the tasks dictionary
tasks = {}

# Global variable for the logged-in user
current_user = ""

# File to store users' credentials
USER_FILE = "users.csv"
TASK_FILE = "tasks.csv"  # Shared task file for all users

# Login Window Function
def login_window():
    def authenticate():
        global current_user
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            with open(USER_FILE, mode='r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == username and row[1] == password:
                        current_user = username
                        login_window_instance.destroy()
                        root.deiconify()
                        user_label.config(text=f"Logged in as: {current_user}")
                        load_tasks_from_csv()
                        return
                messagebox.showerror("Login Failed", "Invalid username or password!")
        else:
            messagebox.showerror("Input Error", "Please enter both username and password!")

    def show_register_window():
        login_window_instance.destroy()
        register_window()

    login_window_instance = tk.Toplevel()
    login_window_instance.title("Login")
    login_window_instance.geometry("300x220")
    login_window_instance.configure(bg="#1E1E2E")

    label = ttk.Label(login_window_instance, text="Login", font=("Segoe UI", 14, "bold"))
    label.pack(pady=10)

    username_label = ttk.Label(login_window_instance, text="Username:")
    username_label.pack()
    username_entry = ttk.Entry(login_window_instance)
    username_entry.pack(pady=5)

    password_label = ttk.Label(login_window_instance, text="Password:")
    password_label.pack()
    password_entry = ttk.Entry(login_window_instance, show="*")
    password_entry.pack(pady=5)

    login_button = ttk.Button(login_window_instance, text="Login", command=authenticate)
    login_button.pack(pady=10)

    register_button = ttk.Button(login_window_instance, text="Register", command=show_register_window)
    register_button.pack()

    login_window_instance.mainloop()

def register_window():
    def register_user():
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            with open(USER_FILE, mode='r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == username:
                        messagebox.showerror("Registration Failed", "Username already exists!")
                        return

            with open(USER_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, password])

            messagebox.showinfo("Success", "You have successfully registered!")
            register_window_instance.destroy()
            login_window()
        else:
            messagebox.showerror("Input Error", "Please enter both username and password!")

    register_window_instance = tk.Toplevel()
    register_window_instance.title("Register")
    register_window_instance.geometry("300x220")
    register_window_instance.configure(bg="#1E1E2E")

    label = ttk.Label(register_window_instance, text="Create Account", font=("Segoe UI", 14, "bold"))
    label.pack(pady=10)

    username_label = ttk.Label(register_window_instance, text="Username:")
    username_label.pack()
    username_entry = ttk.Entry(register_window_instance)
    username_entry.pack(pady=5)

    password_label = ttk.Label(register_window_instance, text="Password:")
    password_label.pack()
    password_entry = ttk.Entry(register_window_instance, show="*")
    password_entry.pack(pady=5)

    register_button = ttk.Button(register_window_instance, text="Register", command=register_user)
    register_button.pack(pady=10)

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

def load_tasks_from_csv():
    task_treeview.delete(*task_treeview.get_children())
    tasks.clear()  # Clear the tasks before reloading
    try:
        with open(get_task_file(), 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if len(row) >= 3:
                    date_obj = datetime.strptime(row[0], "%m/%d/%y").date()
                    task, employee, status = row[1], row[2], row[3] if len(row) > 3 else "Upcoming"
                    tasks.setdefault(date_obj, []).append((task, employee, status))
                    if status != "Removed":
                        task_treeview.insert("", "end", values=(date_obj.strftime("%b/%d/%y"), task, employee, status))
        highlight_dates()
    except FileNotFoundError:
        pass

def highlight_dates():
    cal.calevent_remove('all')
    today = datetime.today().date()
    for date, task_list in tasks.items():
        for task, employee, status in task_list:
            if date > today:
                status = "Upcoming"
            elif date == today:
                status = "Ongoing"
            else:
                status = "Done"
            if status != "Removed":
                cal.calevent_create(date, f'Task: {status}', status)
    for status, color in TASK_COLORS.items():
        cal.tag_config(status, background=color, foreground="white")

def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    try:
        # Adjusted the date format to handle "mm/dd/yyyy"
        date_obj = datetime.strptime(date_str, "%m/%d/%Y").date()
    except ValueError:
        messagebox.showerror("Date Format Error", f"Invalid date format: {date_str}")
        return
    employee = current_user
    if task:
        # Assign status based on the task's date
        if date_obj > datetime.today().date():
            status = "Upcoming"
        elif date_obj == datetime.today().date():
            status = "Ongoing"  # Set to Ongoing if it's today's date
        else:
            status = "Done"
        
        task_treeview.insert("", "end", values=(date_obj.strftime("%b/%d/%y"), task, employee, status))
        tasks.setdefault(date_obj, []).append((task, employee, status))
        task_entry.delete(0, tk.END)
        highlight_dates()
        save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "Task must be filled!")


def remove_task():
    selected_item = task_treeview.selection()
    if selected_item:
        item_values = task_treeview.item(selected_item, "values")
        if item_values:
            date_str, task, employee, status = item_values
            date_obj = datetime.strptime(date_str, "%b/%d/%y").date()
            if date_obj in tasks:
                tasks[date_obj] = [
                    (t, e, "Removed") if (t == task and e == employee) else (t, e, s)
                    for (t, e, s) in tasks[date_obj]
                ]
            task_treeview.delete(selected_item)
            highlight_dates()
            save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "No task selected!")

def mark_task_as_done():
    selected_item = task_treeview.selection()
    if selected_item:
        item_values = task_treeview.item(selected_item, "values")
        if item_values:
            date_str, task, employee, _ = item_values
            date_obj = datetime.strptime(date_str, "%b/%d/%y").date()
            if date_obj in tasks:
                # Update status to 'Done' instead of 'Removed'
                tasks[date_obj] = [
                    (t, e, "Done") if (t == task and e == employee) else (t, e, s)
                    for (t, e, s) in tasks[date_obj]
                ]
            task_treeview.item(selected_item, values=(date_str, task, employee, "Done"))
            highlight_dates()
            save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "No task selected!")

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

root = tk.Tk()
root.title("To-Do Calendar")
root.geometry("1050x680")
root.configure(bg="#1E1E2E")
root.withdraw()

# Style Setup
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#1E1E2E", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", background="#4C566A", foreground="white", font=("Segoe UI", 10), padding=6)
style.map("TButton", background=[("active", "#5E81AC")])
style.configure("TCombobox", fieldbackground="#3B4252", background="#3B4252", foreground="white")
style.configure("Treeview", background="#2E3440", fieldbackground="#2E3440", foreground="white", font=("Segoe UI", 10))
style.configure("Treeview.Heading", background="#4C566A", foreground="white", font=("Segoe UI", 10, "bold"))

user_label = ttk.Label(root, text="")
user_label.pack(anchor="w", padx=10, pady=(10, 0))

logout_button = ttk.Button(root, text="🔒 Logout", command=logout)
logout_button.pack(anchor="w", padx=10, pady=(0, 10))

export_button = ttk.Button(root, text="📄 Export to PDF", command=export_to_pdf)
export_button.pack(anchor="w", padx=10, pady=(0, 10))

main_frame = tk.Frame(root, bg="#1E1E2E")
main_frame.pack(expand=True, fill="both", padx=10, pady=10)

calendar_frame = tk.Frame(main_frame, bg="#1E1E2E")
calendar_frame.pack(side="left", fill="both", expand=True)

cal = Calendar(calendar_frame, selectmode='day', background="#3B4252", foreground="white",
               selectbackground="#5E81AC", headersbackground="#2E3440", font=("Segoe UI", 10), 
               date_pattern="mm/dd/yyyy", cursor="hand2")
cal.pack(expand=True, fill="both")

task_frame = tk.Frame(main_frame, bg="#1E1E2E")
task_frame.pack(side="right", fill="both", expand=True, padx=10)

task_entry = ttk.Entry(task_frame, font=("Segoe UI", 12))
task_entry.pack(pady=10, fill="x")

add_button = ttk.Button(task_frame, text="Add Task", command=add_task)
add_button.pack(pady=5, fill="x")

remove_button = ttk.Button(task_frame, text="Remove Task", command=remove_task)
remove_button.pack(pady=5, fill="x")

mark_done_button = ttk.Button(task_frame, text="Mark as Done", command=mark_task_as_done)
mark_done_button.pack(pady=5, fill="x")

sort_button = ttk.Button(task_frame, text="Sort by Month", command=sort_by_month)
sort_button.pack(pady=5, fill="x")

task_treeview = ttk.Treeview(task_frame, columns=("Date", "Task", "Employee", "Status"), show="headings")
task_treeview.pack(expand=True, fill="y")

for col in task_treeview["columns"]:
    task_treeview.heading(col, text=col)

TASK_COLORS = {
    "Upcoming": "#D08770",
    "Ongoing": "#A3BE8C",
    "Done": "#B48EAD",
    "Removed": "#E5E9F0"
}

login_window()
root.mainloop()
