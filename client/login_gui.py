import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.utility import LearnLiveClient


class LoginWindow:
    """
    Login/Signup window for LearnLive.
    Beautified modern UI (functionality unchanged).
    """

    def __init__(self, client: LearnLiveClient, on_login_success: callable):
        self.client = client
        self.on_login_success = on_login_success
        self.window = None
        self.is_login_mode = True

    def show(self):
        self.window = ttk.Window(themename="darkly")
        self.window.title("LearnLive")
        self.window.geometry("1000x720")
        self.window.resizable(False, False)

        # Center window
        self.window.update_idletasks()
        w, h = 1000, 720
        x = (self.window.winfo_screenwidth() - w) // 2
        y = (self.window.winfo_screenheight() - h) // 2
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        # Entry focus styling
        style = ttk.Style()
        style.map(
            "TEntry",
            fieldbackground=[("focus", "#3a3a3a")],
            bordercolor=[("focus", "#0d6efd")],
        )

        # Root container
        root = ttk.Frame(self.window, padding=40, bootstyle="dark")
        root.pack(fill=BOTH, expand=YES)

        # ---------------- HEADER ----------------
        header = ttk.Frame(root, bootstyle="dark")
        header.pack(pady=(10, 35))

        ttk.Label(
            header,
            text="🎓",
            font=("Segoe UI Emoji", 54),
            bootstyle="inverse-light",
        ).pack()

        ttk.Label(
            header,
            text="LearnLive",
            font=("Segoe UI", 32, "bold"),
            bootstyle="inverse-light",
        ).pack(pady=(6, 2))

        ttk.Label(
            header,
            text="Smart Classroom Management System",
            font=("Segoe UI", 12),
            bootstyle="inverse-secondary",
        ).pack()

        ttk.Separator(root, bootstyle="secondary").pack(fill=X, pady=(0, 30))

        # ---------------- CARD ----------------
        card = ttk.Frame(
            root,
            padding=35,
            bootstyle="dark",
            relief="solid",
            borderwidth=1,
        )
        card.pack(expand=YES)

        self.form_frame = ttk.Frame(card, bootstyle="dark")
        self.form_frame.pack()

        self._build_login_form()

        self.client.set_message_callback(self._handle_server_response)
        self.window.mainloop()

    # ================= FORMS =================

    def _clear_form(self):
        for w in self.form_frame.winfo_children():
            w.destroy()

    def _build_login_form(self):
        self._clear_form()

        self._field_label("Email")
        self.email_entry = self._entry()

        self._field_label("Password", top_pad=18)
        self.password_entry = self._entry(show="•")

        self.login_btn = ttk.Button(
            self.form_frame,
            text="Login",
            command=self._handle_login,
            bootstyle="primary",
            width=28,
        )
        self.login_btn.pack(pady=(30, 20))

        self._switch_row(
            "Don't have an account?",
            "Sign Up",
            self._switch_to_signup,
        )

        self.status_label = self._status_label()

    def _build_signup_form(self):
        self._clear_form()

        self._field_label("Full Name")
        self.name_entry = self._entry()

        self._field_label("Email", top_pad=12)
        self.email_entry = self._entry()

        self._field_label("Password", top_pad=12)
        self.password_entry = self._entry(show="•")

        self._field_label("I am a:", top_pad=18)
        self.role_var = ttk.StringVar(value="student")

        role_frame = ttk.Frame(self.form_frame, bootstyle="dark")
        role_frame.pack(fill=X, pady=(5, 20))

        ttk.Radiobutton(
            role_frame,
            text="Teacher",
            variable=self.role_var,
            value="teacher",
            bootstyle="primary",
        ).pack(side=LEFT, padx=(0, 25))

        ttk.Radiobutton(
            role_frame,
            text="Student",
            variable=self.role_var,
            value="student",
            bootstyle="primary",
        ).pack(side=LEFT)

        self.signup_btn = ttk.Button(
            self.form_frame,
            text="Create Account",
            command=self._handle_signup,
            bootstyle="success",
            width=28,
        )
        self.signup_btn.pack(pady=(10, 18))

        self._switch_row(
            "Already have an account?",
            "Login",
            self._switch_to_login,
        )

        self.status_label = self._status_label()

    # ================= UI HELPERS =================

    def _field_label(self, text, top_pad=0):
        ttk.Label(
            self.form_frame,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bootstyle="inverse-light",
        ).pack(anchor=W, pady=(top_pad, 6))

    def _entry(self, show=None):
        e = ttk.Entry(
            self.form_frame,
            font=("Segoe UI", 12),
            width=42,
            bootstyle="dark",
            show=show,
        )
        e.pack(fill=X)
        return e

    def _switch_row(self, left_text, btn_text, command):
        frame = ttk.Frame(self.form_frame, bootstyle="dark")
        frame.pack(pady=10)

        ttk.Label(
            frame,
            text=left_text,
            font=("Segoe UI", 10),
            bootstyle="inverse-secondary",
        ).pack(side=LEFT, padx=(0, 6))

        ttk.Button(
            frame,
            text=btn_text,
            command=command,
            bootstyle="link-primary",
        ).pack(side=LEFT)

    def _status_label(self):
        lbl = ttk.Label(
            self.form_frame,
            text="",
            font=("Segoe UI", 10),
            bootstyle="danger",
            wraplength=420,
            justify=CENTER,
        )
        lbl.pack(pady=12)
        return lbl

    # ================= MODE SWITCH =================

    def _switch_to_login(self):
        self.is_login_mode = True
        self._build_login_form()

    def _switch_to_signup(self):
        self.is_login_mode = False
        self._build_signup_form()

    # ================= LOGIC (UNCHANGED) =================

    def _handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.status_label.config(text="Please fill all fields")
            return

        self.login_btn.config(state=DISABLED, text="Logging in...")
        self.status_label.config(text="Connecting to server...")

        if not self.client.connected:
            result = self.client.connect()
            if not result["success"]:
                self.status_label.config(text=f"Connection failed: {result['error']}")
                self.login_btn.config(state=NORMAL, text="Login")
                return

        self.client.login(email, password)

    def _handle_signup(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not name or not email or not password:
            self.status_label.config(text="Please fill all fields")
            return

        self.signup_btn.config(state=DISABLED, text="Creating account...")
        self.status_label.config(text="Connecting to server...")

        if not self.client.connected:
            result = self.client.connect()
            if not result["success"]:
                self.status_label.config(text=f"Connection failed: {result['error']}")
                self.signup_btn.config(state=NORMAL, text="Create Account")
                return

        self.client.signup(name, email, password, role)

    def _open_dashboard(self, user_data: dict):
        if self.window:
            self.window.withdraw()
        self.on_login_success(user_data)
        if self.window:
            self.window.after(100, self.window.destroy)

    def _handle_server_response(self, message: dict):
        msg_type = message.get("type", "")

        if msg_type == "SUCCESS":
            if "token" in message:
                self.client.token = message["token"]
                self.client.user_data = {
                    "user_id": message.get("user_id"),
                    "name": message.get("name"),
                    "email": message.get("email"),
                    "role": message.get("role"),
                }
                self.window.after(0, lambda: self._open_dashboard(self.client.user_data))

            elif message.get("message") == "User created successfully":
                self.status_label.config(
                    text="Account created successfully! Please login.",
                    bootstyle="success",
                )
                self._switch_to_login()

        elif msg_type in ("ERROR", "DISCONNECTED"):
            err = message.get("error", "Connection lost. Please try again.")
            self.status_label.config(text=err, bootstyle="danger")

            if self.is_login_mode and hasattr(self, "login_btn"):
                self.login_btn.config(state=NORMAL, text="Login")
            elif hasattr(self, "signup_btn"):
                self.signup_btn.config(state=NORMAL, text="Create Account")
