import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import csv

# Initialize main application
root = tk.Tk()
root.title("Responsive To-Do Calendar")
root.geometry("1000x650")
root.configure(bg="#2C2F33")

# Configure grid to allocate more space to the calendar
root.columnconfigure(0, weight=4)  # Increased weight for the calendar column
root.columnconfigure(1, weight=1)  # Decreased weight for the side panel column
root.rowconfigure(0, weight=1)

# Global Data Storage
tasks = {}  # {date_obj: [(task, employee, status)]}
employees = []

# Color Mapping
TASK_COLORS = {
    "Upcoming": "blue",
    "Ongoing": "yellow",
    "Done": "green"
}

# Function to highlight dates with color-coded tasks
def highlight_dates():
    cal.calevent_remove('all')
    today = datetime.today().date()

    # Loop through each task and highlight dates with color-coded events
    for date, task_list in tasks.items():
        for task, employee, status in task_list:
            # Assign status based on the date and current date
            if date > today:
                status = "Upcoming"
            elif date == today:
                status = "Ongoing"
            else:
                status = "Done"
            cal.calevent_create(date, f'Task: {status}', status)

    # Configure task color tags based on status
    for status, color in TASK_COLORS.items():
        cal.tag_config(status, background=color, foreground="white")

# Function to save tasks
def save_tasks_to_csv():
    with open('tasks.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Task", "Employee", "Status"])
        for date_obj, task_list in tasks.items():
            for task, employee, status in task_list:
                writer.writerow([date_obj.strftime("%m/%d/%y"), task, employee, status])

# Function to load tasks
def load_tasks_from_csv():
    try:
        with open('tasks.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 3:
                    date_obj = datetime.strptime(row[0], "%m/%d/%y").date()
                    task, employee, status = row[1], row[2], row[3] if len(row) > 3 else "Upcoming"
                    tasks.setdefault(date_obj, []).append((task, employee, status))
        highlight_dates()
    except FileNotFoundError:
        pass

# Function to add tasks
def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    date_obj = datetime.strptime(date_str, "%m/%d/%y").date()
    employee = employee_listbox.get(tk.ACTIVE)
    
    if task and employee:
        status = "Upcoming" if date_obj > datetime.today().date() else "Ongoing"
        # Insert task details into the Treeview
        task_treeview.insert("", "end", values=(date_obj.strftime("%m/%d/%y"), task, employee, status))
        tasks.setdefault(date_obj, []).append((task, employee, status))
        task_entry.delete(0, tk.END)
        highlight_dates()
        save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "Task and employee must be selected!")

# Function to remove task
def remove_task():
    selected_item = task_treeview.selection()
    if selected_item:
        task_treeview.delete(selected_item)
    else:
        messagebox.showwarning("Warning", "No task selected!")

# Function to add employees
def add_employee():
    employee_name = employee_entry.get()
    if employee_name:
        employees.append(employee_name)
        employee_listbox.insert(tk.END, employee_name)
        employee_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Employee name cannot be empty!")

# Create Calendar
cal = Calendar(root, selectmode='day', background="#7289DA", foreground="white", selectbackground="darkblue")
cal.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Side Panel
side_panel = ttk.Frame(root, padding=10)
side_panel.grid(row=0, column=1, sticky="nsew")
side_panel.columnconfigure(0, weight=1)
side_panel.rowconfigure(3, weight=1)

# Task Entry
task_entry = ttk.Entry(side_panel, width=30, font=("Arial", 12))
task_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

add_button = ttk.Button(side_panel, text="Add Task", command=add_task)
add_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

remove_button = ttk.Button(side_panel, text="Remove Task", command=remove_task)
remove_button.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

# Task Table (Treeview)
task_treeview = ttk.Treeview(side_panel, columns=("Date", "Task", "Employee", "Status"), show="headings", height=10)
task_treeview.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

# Define columns
task_treeview.heading("Date", text="Date")
task_treeview.heading("Task", text="Task")
task_treeview.heading("Employee", text="Employee")
task_treeview.heading("Status", text="Status")

# Adjust column width
task_treeview.column("Date", width=100, anchor="center")
task_treeview.column("Task", width=250)
task_treeview.column("Employee", width=150)
task_treeview.column("Status", width=100)

# Employee Section
employee_frame = ttk.Frame(side_panel, padding=10)
employee_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

employee_entry = ttk.Entry(employee_frame, width=30)
employee_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

add_employee_button = ttk.Button(employee_frame, text="Add Employee", command=add_employee)
add_employee_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

employee_listbox = tk.Listbox(employee_frame, font=("Arial", 12), selectbackground="#007BFF", selectforeground="white")
employee_listbox.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

remove_employee_button = ttk.Button(employee_frame, text="Remove Employee")
remove_employee_button.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

# Load tasks and make responsive
load_tasks_from_csv()
root.mainloop()
