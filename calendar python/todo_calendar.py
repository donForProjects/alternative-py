import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime
import csv

# Task and employee management
tasks = {}
employees = []

# Function to load tasks from CSV
def load_tasks_from_csv():
    try:
        with open('tasks.csv', mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                if row:
                    date_obj = datetime.strptime(row[0], "%m/%d/%y").date()
                    task, employee = row[1], row[2]
                    tasks.setdefault(date_obj, []).append((task, employee))
        highlight_dates()
    except FileNotFoundError:
        pass

# Function to save tasks to CSV
def save_tasks_to_csv():
    with open('tasks.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(["Date", "Task", "Employee"])
        for date_obj, task_list in tasks.items():
            for task, employee in task_list:
                writer.writerow([date_obj.strftime("%m/%d/%y"), task, employee])

# Add task
def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    date_obj = datetime.strptime(date_str, "%m/%d/%y").date()  # Convert to datetime.date
    employee = employee_listbox.get(tk.ACTIVE)  # Get selected employee
    if task and employee:
        task_list.insert(tk.END, f"{date_str}: {task} (Assigned to {employee})")
        tasks.setdefault(date_obj, []).append((task, employee))
        task_entry.delete(0, tk.END)
        highlight_dates()
        save_tasks_to_csv()  # Save to CSV after adding
    else:
        messagebox.showwarning("Warning", "Task and employee must be selected!")

# Remove task (only from UI, not from the underlying data)
def remove_task():
    try:
        selected_task = task_list.curselection()[0]
        task_text = task_list.get(selected_task)
        task_list.delete(selected_task)

        # Do not remove the task from the tasks dictionary here.
        # The task will remain in the tasks dictionary and be saved back to the CSV when you call save_tasks_to_csv().
        
        # Re-highlight the dates to reflect the current state (with removed tasks from the UI)
        highlight_dates()

    except IndexError:
        messagebox.showwarning("Warning", "No task selected!")

# Edit task
def edit_task():
    try:
        selected_task = task_list.curselection()[0]
        task_text = task_list.get(selected_task)
        date_str, task_employee = task_text.split(": ", 1)
        task, employee = task_employee.rsplit(" (Assigned to ", 1)
        employee = employee.rstrip(")")

        # Parse the date and convert it to date object
        date_obj = datetime.strptime(date_str, "%m/%d/%y").date()

        # Populate the task and employee into the entry field
        task_entry.delete(0, tk.END)
        task_entry.insert(0, task)

        # Remove the task from the list to edit it later
        task_list.delete(selected_task)

        # Add a save button for the edited task
        def save_edited_task():
            new_task = task_entry.get()
            if new_task:
                # Insert the updated task back into the list
                task_list.insert(tk.END, f"{date_str}: {new_task} (Assigned to {employee})")

                # Update the task in the tasks dictionary
                tasks[date_obj] = [(new_task, employee) if t[0] == task else t for t in tasks[date_obj]]

                # Clear the task entry field
                task_entry.delete(0, tk.END)

                # Re-highlight the dates
                highlight_dates()
                save_tasks_to_csv()  # Save to CSV after editing
            else:
                messagebox.showwarning("Warning", "Task cannot be empty!")

        # Add a save button for the edited task
        save_button = tk.Button(side_panel, text="Save Edited Task", command=save_edited_task, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
        save_button.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
    except IndexError:
        messagebox.showwarning("Warning", "No task selected for editing!")

# Highlight dates with tasks
def highlight_dates():
    cal.calevent_remove('all')  # Remove all previous highlights
    for date in tasks.keys():
        cal.calevent_create(date, 'Task', 'task')
    cal.tag_config('task', background='red', foreground='white')

# Add employee
def add_employee():
    employee_name = employee_entry.get()
    if employee_name:
        employees.append(employee_name)
        employee_listbox.insert(tk.END, employee_name)
        employee_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Employee name cannot be empty!")

# Remove employee
def remove_employee():
    try:
        selected_employee = employee_listbox.curselection()[0]
        employee_name = employee_listbox.get(selected_employee)
        employee_listbox.delete(selected_employee)
        employees.remove(employee_name)
    except IndexError:
        messagebox.showwarning("Warning", "No employee selected!")

# Login function
def check_login():
    username = username_entry.get()
    password = password_entry.get()

    # For simplicity, using hardcoded credentials
    if username == "admin" and password == "password123":
        login_window.destroy()
        open_main_app()  # Open the calendar app if login is successful
    else:
        messagebox.showwarning("Login Failed", "Incorrect username or password")

# Function to open main application after successful login
def open_main_app():
    # Create main window
    global root
    root = tk.Tk()
    root.title("To-Do List Calendar")
    root.geometry("900x600")
    root.configure(bg="#f0f0f0")
    root.columnconfigure(0, weight=3)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    # Calendar widget
    global cal
    cal = Calendar(root, selectmode='day', year=2025, month=4, day=2, background="lightblue", foreground="black", headersbackground="blue", headersforeground="white", selectbackground="darkblue", selectforeground="white")
    cal.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Side panel frame
    global side_panel
    side_panel = tk.Frame(root, bg="#ffffff", relief=tk.RIDGE, bd=2)
    side_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    side_panel.columnconfigure(0, weight=1)
    side_panel.rowconfigure(1, weight=1)
    side_panel.rowconfigure(2, weight=1)

    # Task entry
    global task_entry
    task_entry = tk.Entry(side_panel, width=30, font=("Arial", 12))
    task_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

    global add_button
    add_button = tk.Button(side_panel, text="Add Task", command=add_task, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
    add_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
  
    global remove_button
    remove_button = tk.Button(side_panel, text="Remove Task", command=remove_task, bg="#f44336", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
    remove_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    # Task list
    global task_list
    task_list = tk.Listbox(side_panel, font=("Arial", 12), bg="#ffffff", fg="#333333", selectbackground="#007BFF", selectforeground="white")
    task_list.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

    # Employee section
    global employee_frame
    employee_frame = tk.Frame(side_panel, bg="#ffffff")
    employee_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)

    # Employee entry
    global employee_entry
    employee_entry = tk.Entry(employee_frame, width=30, font=("Arial", 12))
    employee_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

    # Add employee button
    global add_employee_button
    add_employee_button = tk.Button(employee_frame, text="Add Employee", command=add_employee, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
    add_employee_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
  
    # Employee listbox
    global employee_listbox
    employee_listbox = tk.Listbox(employee_frame, font=("Arial", 12), bg="#ffffff", fg="#333333", selectbackground="#007BFF", selectforeground="white")
    employee_listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
  
    # Remove employee button
    global remove_employee_button
    remove_employee_button = tk.Button(employee_frame, text="Remove Employee", command=remove_employee, bg="#f44336", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
    remove_employee_button.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    # Now that cal is initialized, call highlight_dates to highlight any tasks
    highlight_dates()

    root.mainloop()


# Create login window
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x250")

# Username entry
username_label = tk.Label(login_window, text="Username:", font=("Arial", 12))
username_label.grid(row=0, column=0, padx=10, pady=10)
username_entry = tk.Entry(login_window, font=("Arial", 12))
username_entry.grid(row=0, column=1, padx=10, pady=10)

# Password entry
password_label = tk.Label(login_window, text="Password:", font=("Arial", 12))
password_label.grid(row=1, column=0, padx=10, pady=10)
password_entry = tk.Entry(login_window, show="*", font=("Arial", 12))
password_entry.grid(row=1, column=1, padx=10, pady=10)

# Login button
login_button = tk.Button(login_window, text="Login", command=check_login, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
login_button.grid(row=2, column=0, columnspan=2,padx=10, pady=20)

login_window.mainloop()
