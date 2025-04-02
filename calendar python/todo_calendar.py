import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime
import csv
import os

tasks = {}
employees = []

# Function to load tasks from the CSV file
def load_tasks_from_csv():
    if os.path.isfile('tasks.csv'):
        with open('tasks.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                date_str, task, employee = row
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert to datetime.date
                tasks.setdefault(date_obj, []).append((task, employee))
        highlight_dates()  # Highlight the loaded dates on the calendar

# Function to save tasks to CSV
def save_tasks_to_csv():
    with open('tasks.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Task', 'Employee'])  # Header for CSV
        for date, task_list in tasks.items():
            for task, employee in task_list:
                writer.writerow([date, task, employee])

# Add task function
def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    date_obj = datetime.strptime(date_str, "%m/%d/%y").date()  # Convert to datetime.date
    employee = employee_listbox.get(tk.ACTIVE)  # Get selected employee
    if task and employee:
        task_list.insert(tk.END, f"{date_str}: {task} (Assigned to {employee})")
        tasks.setdefault(date_obj, []).append((task, employee))
        task_entry.delete(0, tk.END)
        save_tasks_to_csv()  # Save to CSV after adding a task
        highlight_dates()
    else:
        messagebox.showwarning("Warning", "Task and employee must be selected!")

# Remove task function
def remove_task():
    try:
        selected_task = task_list.curselection()[0]
        task_text = task_list.get(selected_task)
        task_list.delete(selected_task)
        date_str, task_employee = task_text.split(": ", 1)
        task, employee = task_employee.rsplit(" (Assigned to ", 1)
        employee = employee.rstrip(")")
        date_obj = datetime.strptime(date_str, "%m/%d/%y").date()
        tasks[date_obj] = [t for t in tasks[date_obj] if t[1] != employee and t[0] != task]
        if not tasks[date_obj]:
            del tasks[date_obj]
        save_tasks_to_csv()  # Save to CSV after removing a task
        highlight_dates()
    except IndexError:
        messagebox.showwarning("Warning", "No task selected!")

# Highlight dates on the calendar
def highlight_dates():
    cal.calevent_remove('all')  # Remove all previous highlights
    for date in tasks.keys():
        cal.calevent_create(date, 'Task', 'task')
    cal.tag_config('task', background='red', foreground='white')

# Add employee function
def add_employee():
    employee_name = employee_entry.get()
    if employee_name:
        employees.append(employee_name)
        employee_listbox.insert(tk.END, employee_name)
        employee_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Employee name cannot be empty!")

# Remove employee function
def remove_employee():
    try:
        selected_employee = employee_listbox.curselection()[0]
        employee_name = employee_listbox.get(selected_employee)
        employee_listbox.delete(selected_employee)
        employees.remove(employee_name)
    except IndexError:
        messagebox.showwarning("Warning", "No employee selected!")

# Create the main window
root = tk.Tk()
root.title("To-Do List Calendar")
root.geometry("900x600")
root.configure(bg="#f0f0f0")
root.columnconfigure(0, weight=3)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Calendar widget
cal = Calendar(root, selectmode='day', year=2025, month=4, day=2, background="lightblue", foreground="black", headersbackground="blue", headersforeground="white", selectbackground="darkblue", selectforeground="white")
cal.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Side panel frame
side_panel = tk.Frame(root, bg="#ffffff", relief=tk.RIDGE, bd=2)
side_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
side_panel.columnconfigure(0, weight=1)
side_panel.rowconfigure(1, weight=1)
side_panel.rowconfigure(2, weight=1)

# Task entry
task_entry = tk.Entry(side_panel, width=30, font=("Arial", 12))
task_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

# Buttons for task management
add_button = tk.Button(side_panel, text="Add Task", command=add_task, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
add_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

remove_button = tk.Button(side_panel, text="Remove Task", command=remove_task, bg="#f44336", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
remove_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

# Task list
task_list = tk.Listbox(side_panel, font=("Arial", 12), bg="#ffffff", fg="#333333", selectbackground="#007BFF", selectforeground="white")
task_list.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

# Employee section
employee_frame = tk.Frame(side_panel, bg="#ffffff")
employee_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)

# Employee entry
employee_entry = tk.Entry(employee_frame, width=30, font=("Arial", 12))
employee_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

# Add employee button
add_employee_button = tk.Button(employee_frame, text="Add Employee", command=add_employee, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
add_employee_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

# Employee listbox
employee_listbox = tk.Listbox(employee_frame, font=("Arial", 12), bg="#ffffff", fg="#333333", selectbackground="#007BFF", selectforeground="white")
employee_listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

# Remove employee button
remove_employee_button = tk.Button(employee_frame, text="Remove Employee", command=remove_employee, bg="#f44336", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
remove_employee_button.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

# Make task list expandable
side_panel.rowconfigure(3, weight=1)

# Load existing tasks from the CSV file at startup
load_tasks_from_csv()

# Run the application
root.mainloop()
