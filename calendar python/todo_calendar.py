import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import csv
import os

# Global variable for the logged-in user
current_user = ""

# File to store users' credentials
USER_FILE = "users.csv"

#the clock
def update_clock():
    now = datetime.now().strftime("%I:%M:%S %p")
    clock_frame.config(text=now)
    root.after(1000, update_clock) 

# Login Window Function
def login_window():
    def authenticate():
        global current_user
        username = username_entry.get()
        password = password_entry.get()

        # Simple authentication for demonstration
        if username and password:
            # Check if username exists in the user file
            with open(USER_FILE, mode='r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == username and row[1] == password:
                        current_user = username  # Set the logged-in username
                        login_window_instance.destroy()  # Close login window
                        root.deiconify()  # Show the main window
                        user_label.config(text=f"Logged in as: {current_user}")  # Display logged-in user
                        populate_employee_dropdown()  # Populate employee dropdown
                        return
                messagebox.showerror("Login Failed", "Invalid username or password!")
        else:
            messagebox.showerror("Input Error", "Please enter both username and password!")

    def show_register_window():
        login_window_instance.destroy()
        register_window()

    # Create Login Window
    login_window_instance = tk.Toplevel()
    login_window_instance.title("Login")
    login_window_instance.geometry("300x200")
    login_window_instance.configure(bg="#2C2F33")
    
    label = ttk.Label(login_window_instance, text="Please login", font=("Arial", 16), background="#2C2F33", foreground="white")
    label.pack(pady=20)

    username_label = ttk.Label(login_window_instance, text="Username:", background="#2C2F33", foreground="white")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(login_window_instance)
    username_entry.pack(pady=5)

    password_label = ttk.Label(login_window_instance, text="Password:", background="#2C2F33", foreground="white")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(login_window_instance, show="*")
    password_entry.pack(pady=5)

    login_button = ttk.Button(login_window_instance, text="Login", command=authenticate)
    login_button.pack(pady=20)

    register_button = ttk.Button(login_window_instance, text="Register", command=show_register_window)
    register_button.pack(pady=5)

    login_window_instance.mainloop()

# Register Window Function
def register_window():
    def register_user():
        username = username_entry.get()
        password = password_entry.get()

        if username and password:
            # Check if the username already exists
            with open(USER_FILE, mode='r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == username:
                        messagebox.showerror("Registration Failed", "Username already exists!")
                        return
            
            # If username is unique, register the user
            with open(USER_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, password])

            messagebox.showinfo("Registration Successful", "You have successfully registered!")
            register_window_instance.destroy()
            login_window()
        else:
            messagebox.showerror("Input Error", "Please enter both username and password!")

    # Create Register Window
    register_window_instance = tk.Toplevel()
    register_window_instance.title("Register")
    register_window_instance.geometry("300x200")
    register_window_instance.configure(bg="#2C2F33")

    label = ttk.Label(register_window_instance, text="Create an account", font=("Arial", 16), background="#2C2F33", foreground="white")
    label.pack(pady=20)

    username_label = ttk.Label(register_window_instance, text="Username:", background="#2C2F33", foreground="white")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(register_window_instance)
    username_entry.pack(pady=5)

    password_label = ttk.Label(register_window_instance, text="Password:", background="#2C2F33", foreground="white")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(register_window_instance, show="*")
    password_entry.pack(pady=5)

    register_button = ttk.Button(register_window_instance, text="Register", command=register_user)
    register_button.pack(pady=20)

    register_window_instance.mainloop()

# Function to get all users from the users.csv file
def get_all_users():
    users = []
    try:
        with open(USER_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                users.append(row[0])  # Add username (first column) to the list
    except FileNotFoundError:
        pass
    return users

# Function to populate the employee dropdown
def populate_employee_dropdown():
    users = get_all_users()  # Get all registered users
    employee_listbox['values'] = users  # Update the combobox with the user list
    if users:  # If there are users, select the first one by default
        employee_listbox.set(users[0])

# Initialize main application
root = tk.Tk()
root.title("Responsive To-Do Calendar")
root.geometry("1000x650")
root.configure(bg="#2C2F33")
root.withdraw()  # Hide the main window initially

# Label to show logged-in user
user_label = ttk.Label(root, text="", font=("Arial", 14), background="#2C2F33", foreground="white")
user_label.grid(row=0, column=0, columnspan=2, pady=10)

# Configure grid to allocate more space to the calendar
root.columnconfigure(0, weight=4)  # Calendar gets more space
root.columnconfigure(1, weight=1)  # Side panel gets less space
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

    for date, task_list in tasks.items():
        for task, employee, status in task_list:
            if date > today:
                status = "Upcoming"
            elif date == today:
                status = "Ongoing"
            else:
                status = "Done"
            cal.calevent_create(date, f'Task: {status}', status)

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
# Function to add tasks
def add_task():
    task = task_entry.get()
    date_str = cal.get_date()
    date_obj = datetime.strptime(date_str, "%m/%d/%y").date()

    # Get the selected employee from the listbox
    selected_employee_index = employee_listbox.curselection()  # Get the index of selected item
    if selected_employee_index:
        employee = employee_listbox.get(selected_employee_index)  # Get the selected employee
    else:
        messagebox.showwarning("Warning", "Please select an employee!")
        return

    if task and employee:
        # In the add_task function
        status = "Upcoming" if date_obj > datetime.today().date() else "Ongoing" if date_obj == datetime.today().date() else "Done"
        task_treeview.insert("", "end", values=(date_obj.strftime("%b/%d/%y"), task, employee, status))
        tasks.setdefault(date_obj, []).append((task, employee, status))
        task_entry.delete(0, tk.END)
        highlight_dates()
        save_tasks_to_csv()
    else:
        messagebox.showwarning("Warning", "Task cannot be empty!")


# Function to remove task
def remove_task():
    selected_item = task_treeview.selection()
    if selected_item:
        # Get selected task values
        item_values = task_treeview.item(selected_item, "values")
        if item_values:
            date_str, task, employee, status = item_values
            date_obj = datetime.strptime(date_str, "%b/%d/%y").date()

            # Remove the task from the dictionary
            if date_obj in tasks:
                tasks[date_obj] = [t for t in tasks[date_obj] if t[:2] != (task, employee)]
                if not tasks[date_obj]:  # Remove empty date entry
                    del tasks[date_obj]

        # Remove task from Treeview
        task_treeview.delete(selected_item)

        # Refresh calendar highlights
        highlight_dates()

        # Save changes to CSV
    else:
        messagebox.showwarning("Warning", "No task selected!")

# Create Calendar (Fixed Size)
calendar_frame = tk.Frame(root, width=700, height=600)  # Increased size
calendar_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
calendar_frame.grid_propagate(False)  # Prevent the frame from resizing

# Create Calendar inside the Frame
cal = Calendar(calendar_frame, selectmode='day', background="#7289DA", 
               foreground="white", selectbackground="darkblue")
cal.pack(expand=True, fill="both")  # Expand to fill the frame


# Side Panel
side_panel = ttk.Frame(root, padding=10)
side_panel.grid(row=0, column=1, sticky="nsew")
side_panel.columnconfigure(0, weight=1)
side_panel.rowconfigure(3, weight=1)

#deputa
clock_frame = ttk.Label(side_panel, font=("Arial", 16))
clock_frame.grid(row=0, column=0, sticky="ew",padx=5,pady=5)
update_clock()

# Task Entry
task_entry = ttk.Entry(side_panel, width=30, font=("Arial", 12))
task_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

add_button = ttk.Button(side_panel, text="Add Task", command=add_task)
add_button.grid(row=1, column=1, sticky="w", padx=2, pady=5)

remove_button = ttk.Button(side_panel, text="Remove Task", command=remove_task)
remove_button.grid(row=1, column=5, sticky="e", padx=2, pady=5)

# Employee Listbox instead of Dropdown
employee_label = ttk.Label(side_panel, text="Assign Employee:", background="#2C2F33", foreground="white")
employee_label.grid(row=3, column=0, pady=5)

# Create the listbox for employees
employee_listbox = tk.Listbox(side_panel, height=6, font=("Arial", 12), selectmode=tk.SINGLE)
employee_listbox.grid(row=4, column=0, pady=5, padx=5)

# Add the list of employees to the listbox
# Function to populate the employee listbox
# Function to populate the employee listbox
def populate_employee_dropdown():
    users = get_all_users()  # Get all registered users
    employee_listbox.delete(0, tk.END)  # Clear the listbox first

    # Add each user to the listbox
    for user in users:
        employee_listbox.insert(tk.END, user)  # Insert user into the listbox

    if users:  # If there are users, select the first one by default
        employee_listbox.select_set(0)


# Task Table (Treeview) with Fixed Height
task_frame = ttk.Frame(side_panel, width=600, height=200)
task_frame.grid(row=2, column=0, sticky="ew", padx=3, pady=3)
task_frame.grid_propagate(False)

# Create Scrollbars for Treeview
tree_scroll_x = ttk.Scrollbar(task_frame, orient="horizontal")
tree_scroll_x.pack(side="bottom", fill="x")

tree_scroll_y = ttk.Scrollbar(task_frame, orient="vertical")
tree_scroll_y.pack(side="right", fill="y")

task_treeview = ttk.Treeview(task_frame, columns=("Date", "Task", "Employee", "Status"),
                             show="headings", yscrollcommand=tree_scroll_y.set, 
                             xscrollcommand=tree_scroll_x.set)
task_treeview.pack(fill="none", expand=True)

task_treeview.heading("Date", text="Date")
task_treeview.heading("Task", text="Task")
task_treeview.heading("Employee", text="Employee")
task_treeview.heading("Status", text="Status")

tree_scroll_y.config(command=task_treeview.yview)
tree_scroll_x.config(command=task_treeview.xview)



load_tasks_from_csv()

# Start with the login window
login_window()
