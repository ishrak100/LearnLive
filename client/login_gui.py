import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import LearnLiveClient

class LoginWindow:
    """
    Login/Signup window for LearnLive.
    Modern UI inspired by Google Classroom.
    """
    
    def __init__(self, client: LearnLiveClient, on_login_success: callable):
        """
        Initialize login window.
        
        Args:
            client: LearnLiveClient instance
            on_login_success: Callback when login successful
        """
        self.client = client
        self.on_login_success = on_login_success
        self.window = None
        self.is_login_mode = True
        
    def show(self):
        """Show the login window."""
        self.window = ttk.Window(themename="darkly")
        self.window.title("LearnLive - Login")
        self.window.geometry("1000x700")
        self.window.resizable(False, False)
        
        # Center window on screen
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configure entry field focus color to white (do this before creating widgets)
        style = ttk.Style()
        style.map('TEntry',
                  fieldbackground=[('focus', '#2b2b2b')],
                  bordercolor=[('focus', 'white')],
                  lightcolor=[('focus', 'white')],
                  darkcolor=[('focus', 'white')])
        
        # Main container with dark background
        main_frame = ttk.Frame(self.window, padding=40, bootstyle="dark")
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Logo/Header
        header_frame = ttk.Frame(main_frame, bootstyle="dark")
        header_frame.pack(pady=(0, 40))
        
        logo_label = ttk.Label(
            header_frame,
            text="🎓",
            font=("Arial", 60),
            bootstyle="inverse-dark"
        )
        logo_label.pack()
        
        title_label = ttk.Label(
            header_frame,
            text="LearnLive",
            font=("Arial", 32, "bold"),
            bootstyle="inverse-light"
        )
        title_label.pack(pady=(5, 0))
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Classroom Management System",
            font=("Arial", 13),
            bootstyle="inverse-secondary"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Form container with card-like styling
        form_container = ttk.Frame(main_frame, bootstyle="dark")
        form_container.pack(fill=BOTH, expand=YES)
        
        # Center the form
        self.form_frame = ttk.Frame(form_container, bootstyle="dark")
        self.form_frame.pack(expand=YES)
        
        # Build login form
        self._build_login_form()
        
        # Setup message callback
        self.client.set_message_callback(self._handle_server_response)
        
        self.window.mainloop()
    
    def _build_login_form(self):
        """Build login form."""
        # Clear existing widgets
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        
        # Email field
        email_label = ttk.Label(
            self.form_frame,
            text="Email",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        email_label.pack(anchor=W, pady=(10, 5))
        
        self.email_entry = ttk.Entry(
            self.form_frame,
            font=("Arial", 13),
            width=45
        )
        self.email_entry.pack(fill=X, pady=(0, 20))
        
        # Password field
        password_label = ttk.Label(
            self.form_frame,
            text="Password",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        password_label.pack(anchor=W, pady=(0, 5))
        
        self.password_entry = ttk.Entry(
            self.form_frame,
            show="•",
            font=("Arial", 13),
            width=45
        )
        self.password_entry.pack(fill=X, pady=(0, 25))
        
        # Login button
        self.login_btn = ttk.Button(
            self.form_frame,
            text="Login",
            command=self._handle_login,
            bootstyle="secondary",
            width=25
        )
        self.login_btn.pack(pady=(0, 20))
        
        # Switch to signup link
        switch_frame = ttk.Frame(self.form_frame, bootstyle="dark")
        switch_frame.pack(pady=10)
        
        switch_label = ttk.Label(
            switch_frame,
            text="Don't have an account?",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        switch_label.pack(side=LEFT, padx=(0, 5))
        
        switch_btn = ttk.Button(
            switch_frame,
            text="Sign Up",
            command=self._switch_to_signup,
            bootstyle="link"
        )
        switch_btn.pack(side=LEFT)
        
        # Status message
        self.status_label = ttk.Label(
            self.form_frame,
            text="",
            font=("Arial", 11),
            bootstyle="danger"
        )
        self.status_label.pack(pady=15)
    
    def _build_signup_form(self):
        """Build signup form."""
        # Clear existing widgets
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        
        # Name field
        name_label = ttk.Label(
            self.form_frame,
            text="Full Name",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        name_label.pack(anchor=W, pady=(5, 5))
        
        self.name_entry = ttk.Entry(
            self.form_frame,
            font=("Arial", 13),
            width=45
        )
        self.name_entry.pack(fill=X, pady=(0, 12))
        
        # Email field
        email_label = ttk.Label(
            self.form_frame,
            text="Email",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        email_label.pack(anchor=W, pady=(0, 5))
        
        self.email_entry = ttk.Entry(
            self.form_frame,
            font=("Arial", 13),
            width=45
        )
        self.email_entry.pack(fill=X, pady=(0, 12))
        
        # Password field
        password_label = ttk.Label(
            self.form_frame,
            text="Password",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        password_label.pack(anchor=W, pady=(0, 5))
        
        self.password_entry = ttk.Entry(
            self.form_frame,
            show="•",
            font=("Arial", 13),
            width=45
        )
        self.password_entry.pack(fill=X, pady=(0, 12))
        
        # Role selection
        role_label = ttk.Label(
            self.form_frame,
            text="I am a:",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        role_label.pack(anchor=W, pady=(0, 8))
        
        self.role_var = ttk.StringVar(value="student")
        
        role_frame = ttk.Frame(self.form_frame, bootstyle="dark")
        role_frame.pack(fill=X, pady=(0, 15))
        
        teacher_radio = ttk.Radiobutton(
            role_frame,
            text="Teacher",
            variable=self.role_var,
            value="teacher",
            bootstyle="primary"
        )
        teacher_radio.pack(side=LEFT, padx=(0, 20))
        
        student_radio = ttk.Radiobutton(
            role_frame,
            text="Student",
            variable=self.role_var,
            value="student",
            bootstyle="primary"
        )
        student_radio.pack(side=LEFT)
        
        # Signup button
        self.signup_btn = ttk.Button(
            self.form_frame,
            text="Sign Up",
            command=self._handle_signup,
            bootstyle="secondary",
            width=25
        )
        self.signup_btn.pack(pady=(0, 15))
        
        # Switch to login link
        switch_frame = ttk.Frame(self.form_frame, bootstyle="dark")
        switch_frame.pack(pady=5)
        
        switch_label = ttk.Label(
            switch_frame,
            text="Already have an account?",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        switch_label.pack(side=LEFT, padx=(0, 5))
        
        switch_btn = ttk.Button(
            switch_frame,
            text="Login",
            command=self._switch_to_login,
            bootstyle="link"
        )
        switch_btn.pack(side=LEFT)
        
        # Status message
        self.status_label = ttk.Label(
            self.form_frame,
            text="",
            font=("Arial", 11),
            bootstyle="danger"
        )
        self.status_label.pack(pady=5)
    
    def _switch_to_login(self):
        """Switch to login mode."""
        self.is_login_mode = True
        # Clear old button references
        if hasattr(self, 'signup_btn'):
            del self.signup_btn
        if hasattr(self, 'name_entry'):
            del self.name_entry
        if hasattr(self, 'role_var'):
            del self.role_var
        self._build_login_form()
    
    def _switch_to_signup(self):
        """Switch to signup mode."""
        self.is_login_mode = False
        # Clear old button references
        if hasattr(self, 'login_btn'):
            del self.login_btn
        self._build_signup_form()
    
    def _handle_login(self):
        """Handle login button click."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Validate
        if not email or not password:
            self.status_label.config(text="Please fill all fields")
            return
        
        # Disable button
        self.login_btn.config(state=DISABLED, text="Logging in...")
        self.status_label.config(text="Connecting to server...")
        
        # Connect to server if not connected
        if not self.client.connected:
            result = self.client.connect()
            if not result["success"]:
                self.status_label.config(text=f"Connection failed: {result['error']}")
                self.login_btn.config(state=NORMAL, text="Login")
                return
        
        # Send login request
        self.client.login(email, password)
    
    def _handle_signup(self):
        """Handle signup button click."""
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()
        
        # Validate
        if not name or not email or not password:
            self.status_label.config(text="Please fill all fields")
            return
        
        # Prevent double-click
        if hasattr(self, 'signup_btn') and str(self.signup_btn.cget('state')) == 'disabled':
            return
        
        # Disable button
        self.signup_btn.config(state=DISABLED, text="Creating account...")
        self.status_label.config(text="Connecting to server...")
        
        # Connect to server if not connected
        if not self.client.connected:
            result = self.client.connect()
            if not result["success"]:
                self.status_label.config(text=f"Connection failed: {result['error']}")
                self.signup_btn.config(state=NORMAL, text="Sign Up")
                return
        
        # Send signup request
        print(f"📤 Sending signup request for {email}")
        self.client.signup(name, email, password, role)
    
    def _open_dashboard(self, user_data: dict):
        """
        Open dashboard (called on main thread).
        
        Args:
            user_data: User information
        """
        # Close login window
        if self.window:
            self.window.withdraw()
            
        # Call success callback to create dashboard
        self.on_login_success(user_data)
        
        # Destroy login window after dashboard is created
        if self.window:
            self.window.after(100, self.window.destroy)
    
    def _handle_server_response(self, message: dict):
        """
        Handle response from server.
        
        Args:
            message: Server response message
        """
        msg_type = message.get("type", "")
        
        # DEBUG: Print handling
        print(f"🔍 LoginGUI handling response: type={msg_type}, message={message}")
        
        if msg_type == "SUCCESS":
            # Check if login response (has token)
            if "token" in message:
                # Login successful
                self.client.token = message["token"]
                self.client.user_data = {
                    "user_id": message.get("user_id"),
                    "name": message.get("name"),
                    "email": message.get("email"),
                    "role": message.get("role")
                }
                
                # Schedule dashboard creation on main thread (thread-safe)
                if self.window:
                    self.window.after(0, lambda: self._open_dashboard(self.client.user_data))
            
            elif message.get("message") == "User created successfully":
                # Signup successful - switch to login
                print("✅ Signup successful, switching to login")
                self.status_label.config(
                    text="Account created! Please login.",
                    bootstyle="success"
                )
                self._switch_to_login()
                
                # Re-enable signup button
                if hasattr(self, 'signup_btn'):
                    self.signup_btn.config(state=NORMAL, text="Sign Up")
        
        elif msg_type == "ERROR":
            # Show error
            error_msg = message.get("error", "Unknown error")
            
            # Truncate very long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            print(f"❌ Error: {error_msg}")
            
            # Only update status if window still exists
            if self.status_label.winfo_exists():
                self.status_label.config(text=error_msg, bootstyle="danger")
            
            # Re-enable buttons only if they exist and are valid
            try:
                if self.is_login_mode and hasattr(self, 'login_btn') and self.login_btn.winfo_exists():
                    self.login_btn.config(state=NORMAL, text="Login")
                elif hasattr(self, 'signup_btn') and self.signup_btn.winfo_exists():
                    self.signup_btn.config(state=NORMAL, text="Sign Up")
            except Exception as e:
                print(f"Warning: Could not re-enable button: {e}")
        
        elif msg_type == "DISCONNECTED":
            # Connection lost
            if self.status_label.winfo_exists():
                self.status_label.config(
                    text="Connection lost. Please try again.",
                    bootstyle="danger"
                )
            
            # Re-enable buttons only if they exist and are valid
            try:
                if self.is_login_mode and hasattr(self, 'login_btn') and self.login_btn.winfo_exists():
                    self.login_btn.config(state=NORMAL, text="Login")
                elif hasattr(self, 'signup_btn') and self.signup_btn.winfo_exists():
                    self.signup_btn.config(state=NORMAL, text="Sign Up")
            except Exception as e:
                print(f"Warning: Could not re-enable button: {e}")


