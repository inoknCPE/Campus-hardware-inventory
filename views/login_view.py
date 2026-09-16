try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    tk = None
    messagebox = None
    ttk = None
    TKINTER_AVAILABLE = False

from controllers.auth_controller import AuthController
from logger import logger

class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = AuthController()
        self.lockout_job = None
        self.build_ui()

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("System Auth - Login/Register")
        self.root.geometry("480x360")
        self.root.resizable(False, False)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.login_tab = ttk.Frame(self.notebook)
        self.register_tab = ttk.Frame(self.notebook)
        self.reset_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.login_tab, text="Login")
        self.notebook.add(self.register_tab, text="Register")
        self.notebook.add(self.reset_tab, text="Reset Password")
        self.notebook.select(self.login_tab)

        self._build_login_tab()
        self._build_register_tab()
        self._build_reset_tab()

    def _build_login_tab(self):
        tk.Label(self.login_tab, text="User Authentication", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(self.login_tab, text="Username:").pack(anchor="w", padx=40)
        user_frame = tk.Frame(self.login_tab)
        user_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_user = tk.Entry(user_frame, width=32)
        self.entry_user.pack(side="left", fill="x", expand=True)

        tk.Label(self.login_tab, text="Password:").pack(anchor="w", padx=40)
        pass_frame = tk.Frame(self.login_tab)
        pass_frame.pack(pady=(0, 15), padx=40, fill="x")
        self.entry_pass = tk.Entry(pass_frame, width=26, show="*")
        self.entry_pass.pack(side="left", fill="x", expand=True)

        self.show_login_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(pass_frame, text="Show password", variable=self.show_login_pass_var,
        command=self._toggle_login_password).pack(side="right", padx=(8, 0))
        self.lockout_label = tk.Label(self.login_tab, text="", fg="red", font=("Arial", 9, "bold"))
        self.lockout_label.pack(pady=(0, 5))

        tk.Button(self.login_tab, text="Login", command=self.handle_login, bg="#4CAF50", fg="white", width=12).pack(pady=5)

    def _update_lockout_countdown(self):
        username = self.entry_user.get().strip()
        remaining = self.auth.get_lockout_remaining(username)
        # -1 => locked until password reset
        if remaining < 0:
            self.lockout_label.config(text="Account locked. Reset your password using the Reset Password tab.")
            self.lockout_job = None
        else:
            self.lockout_label.config(text="")
            self.lockout_job = None

    def _cancel_lockout_countdown(self):
        if self.lockout_job is not None:
            self.root.after_cancel(self.lockout_job)
            self.lockout_job = None

    def _toggle_login_password(self):
        if getattr(self, 'show_login_pass_var', None) and self.show_login_pass_var.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def _toggle_register_password(self):
        if getattr(self, 'show_register_pass_var', None) and self.show_register_pass_var.get():
            self.entry_register_pass.config(show="")
        else:
            self.entry_register_pass.config(show="*")

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        remaining = self.auth.get_lockout_remaining(username)
        if remaining < 0:
            self.lockout_label.config(text="Account locked. Reset your password using the Reset Password tab.")
            return

        success, msg = self.auth.login_user(username, password)
        if success:
            self._cancel_lockout_countdown()
            self.lockout_label.config(text="")
            messagebox.showinfo("Success", msg)
            self.on_login_success(username)
        else:
            if "locked" in msg.lower():
                # no countdown for persistent lock; show message instead
                self.lockout_label.config(text="Account locked. Reset your password using the Reset Password tab.")
            else:
                self._cancel_lockout_countdown()
                self.lockout_label.config(text="")
            messagebox.showerror("Authentication Failed", msg)

    def _build_reset_tab(self):
        tk.Label(self.reset_tab, text="Reset Password", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(self.reset_tab, text="Username:").pack(anchor="w", padx=40)
        user_frame = tk.Frame(self.reset_tab)
        user_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_reset_user = tk.Entry(user_frame, width=32)
        self.entry_reset_user.pack(side="left", fill="x", expand=True)

        tk.Label(self.reset_tab, text="Email:").pack(anchor="w", padx=40)
        email_frame = tk.Frame(self.reset_tab)
        email_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_reset_email = tk.Entry(email_frame, width=32)
        self.entry_reset_email.pack(side="left", fill="x", expand=True)

        tk.Label(self.reset_tab, text="New Password:").pack(anchor="w", padx=40)
        new_pass_frame = tk.Frame(self.reset_tab)
        new_pass_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_reset_pass = tk.Entry(new_pass_frame, width=26, show="*")
        self.entry_reset_pass.pack(side="left", fill="x", expand=True)
        # show/hide checkbox for new password (shares same variable as confirm)
        self.show_reset_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(new_pass_frame, text="Show password", variable=self.show_reset_pass_var,
             command=self._toggle_reset_password).pack(side="right", padx=(8, 0))

        tk.Label(self.reset_tab, text="Confirm New Password:").pack(anchor="w", padx=40)
        confirm_pass_frame = tk.Frame(self.reset_tab)
        confirm_pass_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_reset_pass_confirm = tk.Entry(confirm_pass_frame, width=26, show="*")
        self.entry_reset_pass_confirm.pack(side="left", fill="x", expand=True)

        tk.Checkbutton(confirm_pass_frame, text="Show password", variable=self.show_reset_pass_var,
            command=self._toggle_reset_password).pack(side="right", padx=(8, 0))

        tk.Button(self.reset_tab, text="Reset Password", command=self.handle_reset, bg="#f44336", fg="white", width=14).pack(pady=5)

    def _toggle_reset_password(self):
        if getattr(self, 'show_reset_pass_var', None) and self.show_reset_pass_var.get():
            self.entry_reset_pass.config(show="")
            self.entry_reset_pass_confirm.config(show="")
        else:
            self.entry_reset_pass.config(show="*")
            self.entry_reset_pass_confirm.config(show="*")

    def handle_reset(self):
        username = self.entry_reset_user.get().strip()
        email = self.entry_reset_email.get().strip()
        new_pw = self.entry_reset_pass.get().strip()
        confirm_pw = self.entry_reset_pass_confirm.get().strip()

        if not username or not email or not new_pw or not confirm_pw:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if new_pw != confirm_pw:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        success, msg = self.auth.reset_password(username, email, new_pw)
        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.login_tab)
            try:
                self.entry_reset_user.delete(0, tk.END)
                self.entry_reset_email.delete(0, tk.END)
                self.entry_reset_pass.delete(0, tk.END)
                self.entry_reset_pass_confirm.delete(0, tk.END)
                self.show_reset_pass_var.set(False)
            except Exception:
                pass
        else:
            messagebox.showerror("Reset Failed", msg)

    def handle_register(self):
        username = self.entry_register_user.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_register_pass.get().strip()
        role = self.role_var.get()

        success, msg = self.auth.register_user(username, email, password, role=role)
        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.login_tab)
            # Clear register inputs so they are empty next time user opens Register tab
            try:
                self.entry_register_user.delete(0, tk.END)
                self.entry_email.delete(0, tk.END)
                self.entry_register_pass.delete(0, tk.END)
                if getattr(self, 'show_register_pass_var', None):
                    self.show_register_pass_var.set(False)
            except Exception:
                pass
        else:
            messagebox.showerror("Registration Failed", msg)

    def _build_register_tab(self):
        tk.Label(self.register_tab, text="Create an Account", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(self.register_tab, text="Username:").pack(anchor="w", padx=40)
        reg_user_frame = tk.Frame(self.register_tab)
        reg_user_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_register_user = tk.Entry(reg_user_frame, width=32)
        self.entry_register_user.pack(side="left", fill="x", expand=True)

        tk.Label(self.register_tab, text="Email:").pack(anchor="w", padx=40)
        email_frame = tk.Frame(self.register_tab)
        email_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_email = tk.Entry(email_frame, width=32)
        self.entry_email.pack(side="left", fill="x", expand=True)

        tk.Label(self.register_tab, text="Role:").pack(anchor="w", padx=40)
        role_frame = tk.Frame(self.register_tab)
        role_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.role_var = tk.StringVar(value='user')
        tk.OptionMenu(role_frame, self.role_var, 'user', 'admin').pack(side="left", fill="x", expand=True)

        tk.Label(self.register_tab, text="Password:").pack(anchor="w", padx=40)
        reg_pass_frame = tk.Frame(self.register_tab)
        reg_pass_frame.pack(pady=(0, 15), padx=40, fill="x")
        self.entry_register_pass = tk.Entry(reg_pass_frame, width=26, show="*")
        self.entry_register_pass.pack(side="left", fill="x", expand=True)
        # show/hide password checkbox positioned at the right of the entry
        self.show_register_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(reg_pass_frame, text="Show password", variable=self.show_register_pass_var,
               command=self._toggle_register_password).pack(side="right", padx=(8, 0))
        tk.Button(self.register_tab, text="Register", command=self.handle_register, bg="#2196F3", fg="white", width=12).pack(pady=5)

    def _toggle_login_password(self):
        if getattr(self, 'show_login_pass_var', None) and self.show_login_pass_var.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def _toggle_register_password(self):
        if getattr(self, 'show_register_pass_var', None) and self.show_register_pass_var.get():
            self.entry_register_pass.config(show="")
        else:
            self.entry_register_pass.config(show="*")

    
class RegisterWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = AuthController()
        self.build_ui()

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("System Auth - Login/Register")
        self.root.geometry("480x360")
        self.root.resizable(False, False)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.login_tab = ttk.Frame(self.notebook)
        self.register_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.login_tab, text="Login")
        self.notebook.add(self.register_tab, text="Register")
        self.notebook.select(self.register_tab)

        self._build_login_tab()
        self._build_register_tab()

    def _build_login_tab(self):
        tk.Label(self.login_tab, text="User Authentication", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(self.login_tab, text="Username:").pack(anchor="w", padx=40)
        reg_login_user_frame = tk.Frame(self.login_tab)
        reg_login_user_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_user = tk.Entry(reg_login_user_frame, width=32)
        self.entry_user.pack(side="left", fill="x", expand=True)

        tk.Label(self.login_tab, text="Password:").pack(anchor="w", padx=40)
        pass_frame = tk.Frame(self.login_tab)
        pass_frame.pack(pady=(0, 15), padx=40, fill="x")
        self.entry_pass = tk.Entry(pass_frame, width=26, show="*")
        self.entry_pass.pack(side="left", fill="x", expand=True)
        self.show_login_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(pass_frame, text="Show password", variable=self.show_login_pass_var,
               command=self._toggle_login_password).pack(side="right", padx=(8, 0))
        tk.Button(self.login_tab, text="Login", command=self.handle_login, bg="#4CAF50", fg="white", width=12).pack(pady=5)

    def _build_register_tab(self):
        tk.Label(self.register_tab, text="Create an Account", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(self.register_tab, text="Username:").pack(anchor="w", padx=40)
        reg_user_frame = tk.Frame(self.register_tab)
        reg_user_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_register_user = tk.Entry(reg_user_frame, width=32)
        self.entry_register_user.pack(side="left", fill="x", expand=True)

        tk.Label(self.register_tab, text="Email:").pack(anchor="w", padx=40)
        reg_email_frame = tk.Frame(self.register_tab)
        reg_email_frame.pack(pady=(0, 10), padx=40, fill="x")
        self.entry_email = tk.Entry(reg_email_frame, width=32)
        self.entry_email.pack(side="left", fill="x", expand=True)

        tk.Label(self.register_tab, text="Password:").pack(anchor="w", padx=40)
        reg_pass_frame = tk.Frame(self.register_tab)
        reg_pass_frame.pack(pady=(0, 15), padx=40, fill="x")
        self.entry_register_pass = tk.Entry(reg_pass_frame, width=26, show="*")
        self.entry_register_pass.pack(side="left", fill="x", expand=True)
        self.show_register_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(reg_pass_frame, text="Show password", variable=self.show_register_pass_var,
               command=self._toggle_register_password).pack(side="right", padx=(8, 0))
        tk.Button(self.register_tab, text="Register", command=self.handle_register, bg="#2196F3", fg="white", width=12).pack(pady=5)
    def _toggle_login_password(self):
        if getattr(self, 'show_login_pass_var', None) and self.show_login_pass_var.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def _toggle_register_password(self):
        if getattr(self, 'show_register_pass_var', None) and self.show_register_pass_var.get():
            self.entry_register_pass.config(show="")
        else:
            self.entry_register_pass.config(show="*")
    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        success, msg = self.auth.login_user(username, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.on_login_success(username)
        else:
            messagebox.showerror("Authentication Failed", msg)

    def handle_register(self):
        username = self.entry_register_user.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_register_pass.get().strip()
        role = self.role_var.get() if getattr(self, 'role_var', None) else 'user'

        success, msg = self.auth.register_user(username, email, password, role)
        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.login_tab)
            # Clear register inputs so they are empty next time user opens Register tab
            try:
                self.entry_register_user.delete(0, tk.END)
                self.entry_email.delete(0, tk.END)
                self.entry_register_pass.delete(0, tk.END)
                if getattr(self, 'show_register_pass_var', None):
                    self.show_register_pass_var.set(False)
            except Exception:
                pass
        else:
            messagebox.showerror("Registration Failed", msg)