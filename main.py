import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    print("Using PostgreSQL connection from DATABASE_URL.")
else:
    print("DATABASE_URL not set; falling back to local SQLite database.")

try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    tk = None
    messagebox = None
    ttk = None
    TKINTER_AVAILABLE = False

from models.database import init_db
from views.login_view import LoginWindow, RegisterWindow
from views.tracker_view import TrackerWindow

def launch_main_app(username):
    for widget in root.winfo_children():
        widget.destroy()
    TrackerWindow(root, username=username, on_logout=show_login)

def show_login():
    for widget in root.winfo_children():
        widget.destroy()
    LoginWindow(root, on_login_success=launch_main_app)
    
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    show_login()
    root.mainloop()