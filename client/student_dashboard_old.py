import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, Canvas, simpledialog
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.utility import LearnLiveClient

class StudentDashboard:
    """
    Student Dashboard for LearnLive - Google Classroom Style.
    Provides all student features in a modern UI.
    """
    
    def __init__(self, client: LearnLiveClient, user_data: dict):
        """
        Initialize student dashboard.
        
        Args:
            client: LearnLiveClient instance
            user_data: User information
        """
        self.client = client
        self.user_data = user_data
        self.window = None
        self.classes = []  # Will be loaded from server
        self.selected_class = None
        self.current_view = "home"
        self.sidebar = None
        self.content_frame = None
        
        # Setup message callback
        self.client.set_message_callback(self._handle_server_message)
    
    def show(self):
        """Show the student dashboard."""
        self.window = ttk.Window(themename="darkly")
        self.window.title(f"LearnLive - {self.user_data.get('name', 'Student')}")
        self.window.geometry("1400x900")
        
        # Setup window close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=BOTH, expand=YES)
        
        # Sidebar
        self.sidebar = self._create_sidebar(main_container)
        self.sidebar.pack(side=LEFT, fill=Y)
        
        # Right container (header + content)
        right_container = ttk.Frame(main_container)
        right_container.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # Header
        self._create_header(right_container).pack(side=TOP, fill=X)
        
        # Content area
        self.content_frame = ttk.Frame(right_container)
        self.content_frame.pack(side=TOP, fill=BOTH, expand=YES)
        
        # Load classes from server and show home
        self.client.view_classes()
        self._show_home_page()
        
        self.window.mainloop()
    
    def _create_sidebar(self, parent):
        """Create left sidebar"""
        sidebar = ttk.Frame(parent, style="dark", width=280)
        sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = ttk.Frame(sidebar, style="dark")
        logo_frame.pack(fill=X, pady=20, padx=20)
        
        ttk.Label(
            logo_frame,
            text="🎓 LearnLive",
            font=("Arial", 20, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W)
        
        # Navigation
        nav_frame = ttk.Frame(sidebar, style="dark")
        nav_frame.pack(fill=X, padx=10, pady=10)
        
        self.home_btn = ttk.Button(
            nav_frame,
            text="🏠  Home",
            command=self._show_home_page,
            bootstyle="primary",
            width=25
        )
        self.home_btn.pack(fill=X, pady=2)
        
        ttk.Button(nav_frame, text="📅  Calendar", bootstyle="dark", width=25).pack(fill=X, pady=2)
        ttk.Button(nav_frame, text="📚  Enrolled", bootstyle="dark", width=25).pack(fill=X, pady=2)
        ttk.Button(nav_frame, text="✓  To-Do", bootstyle="dark", width=25).pack(fill=X, pady=2)
        
        # Separator
        ttk.Separator(sidebar, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Classes section
        ttk.Label(
            sidebar,
            text="Enrolled Classes",
            font=("Arial", 11, "bold"),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=20, pady=(10, 5))
        
        # Scrollable classes list
        self.classes_frame = ttk.Frame(sidebar, style="dark")
        self.classes_frame.pack(fill=BOTH, expand=YES, padx=10)
        
        return sidebar
    
    def _update_sidebar_classes(self):
        """Update sidebar with current classes"""
        for widget in self.classes_frame.winfo_children():
            widget.destroy()
        
        if not self.classes:
            ttk.Label(
                self.classes_frame,
                text="No classes yet\nJoin a class!",
                font=("Arial", 10),
                bootstyle="inverse-secondary",
                justify=CENTER
            ).pack(pady=20)
            return
        
        canvas = Canvas(self.classes_frame, bg="#222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.classes_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for cls in self.classes:
            btn = ttk.Button(
                scrollable_frame,
                text=f"📖  {cls.get('class_name', 'Unknown')}",
                command=lambda c=cls: self._show_class_page(c),
                bootstyle="dark",
                width=25
            )
            btn.pack(fill=X, pady=2, padx=5)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _create_header(self, parent):
        """Create top header"""
        header = ttk.Frame(parent, bootstyle="dark")
        
        # Search
        search_frame = ttk.Frame(header, bootstyle="dark")
        search_frame.pack(side=LEFT, fill=X, expand=YES, padx=20, pady=15)
        
        search_entry = ttk.Entry(search_frame, font=("Arial", 12), width=50)
        search_entry.insert(0, "🔍 Search classes...")
        search_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # User section
        user_frame = ttk.Frame(header, bootstyle="dark")
        user_frame.pack(side=RIGHT, padx=20)
        
        ttk.Button(
            user_frame,
            text="+ Join Class",
            bootstyle="primary",
            command=self._join_class_dialog
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            user_frame,
            text=f"👤 {self.user_data.get('name', 'User')}",
            bootstyle="secondary-outline",
        ).pack(side=LEFT, padx=5)
        
        return header
    
    def _show_home_page(self):
        """Show home page with class cards"""
        self.current_view = "home"
        self.selected_class = None
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Highlight home button
        if hasattr(self, 'home_btn'):
            self.home_btn.configure(bootstyle="primary")
        
        # Title
        title_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        title_frame.pack(fill=X, padx=30, pady=20)
        
        ttk.Label(
            title_frame,
            text="Your Classes",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W)
        
        # Check if no classes
        if not self.classes:
            self._show_empty_state()
            return
        
        # Scrollable canvas for cards
        canvas = Canvas(self.content_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create grid of class cards
        cards_container = ttk.Frame(scrollable_frame, bootstyle="dark")
        cards_container.pack(fill=BOTH, expand=YES, padx=30, pady=10)
        
        row, col = 0, 0
        for cls in self.classes:
            card = self._create_class_card(cards_container, cls)
            card.grid(row=row, column=col, padx=15, pady=15, sticky=NSEW)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        for i in range(3):
            cards_container.columnconfigure(i, weight=1)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _show_empty_state(self):
        """Show empty state when no classes"""
        empty_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        empty_frame.pack(fill=BOTH, expand=YES)
        
        # Center content
        center_frame = ttk.Frame(empty_frame, bootstyle="dark")
        center_frame.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        ttk.Label(
            center_frame,
            text="📚",
            font=("Arial", 80),
            bootstyle="inverse-secondary"
        ).pack(pady=20)
        
        ttk.Label(
            center_frame,
            text="No classes yet",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(pady=10)
        
        ttk.Label(
            center_frame,
            text="Join a class using the class code from your teacher",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        ).pack(pady=5)
        
        ttk.Button(
            center_frame,
            text="+ Join Class",
            bootstyle="primary",
            command=self._join_class_dialog,
            width=20
        ).pack(pady=20)
    
    def _create_class_card(self, parent, class_data):
        """Create a class card"""
        colors = ["#1967D2", "#0D652D", "#B80672", "#E37400", "#174EA6", "#9334E6"]
        color = colors[hash(class_data.get('_id', '')) % len(colors)]
        
        card = ttk.Frame(parent, bootstyle="secondary", relief=RAISED)
        card.configure(width=350, height=280)
        card.pack_propagate(False)
        
        # Color bar
        color_label = ttk.Label(card, text="", background=color)
        color_label.pack(fill=X, ipady=50)
        
        # Class name on color bar
        name_frame = ttk.Frame(card)
        name_frame.place(relx=0.05, rely=0.15, anchor=W)
        
        ttk.Label(
            name_frame,
            text=class_data.get('class_name', 'Unknown'),
            font=("Arial", 18, "bold"),
            foreground="white",
            background=color
        ).pack(anchor=W)
        
        # Content
        content = ttk.Frame(card, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        ttk.Label(
            content,
            text=class_data.get('teacher_name', 'Teacher'),
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        ttk.Frame(content).pack(fill=BOTH, expand=YES)
        
        # Icons
        icons = ttk.Frame(content, bootstyle="secondary")
        icons.pack(side=BOTTOM, fill=X)
        
        ttk.Label(icons, text="📝", font=("Arial", 16)).pack(side=LEFT, padx=5)
        ttk.Label(icons, text="📁", font=("Arial", 16)).pack(side=LEFT, padx=5)
        
        # Make clickable
        def on_click(e):
            self._show_class_page(class_data)
        
        card.bind("<Button-1>", on_click)
        color_label.bind("<Button-1>", on_click)
        
        return card
    
    def _show_class_page(self, class_data):
        """Show class detail page"""
        self.current_view = "class"
        self.selected_class = class_data
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update sidebar
        if hasattr(self, 'home_btn'):
            self.home_btn.configure(bootstyle="dark")
        
        # Banner
        colors = ["#1967D2", "#0D652D", "#B80672", "#E37400", "#174EA6", "#9334E6"]
        color = colors[hash(class_data.get('_id', '')) % len(colors)]
        
        banner = ttk.Frame(self.content_frame, height=150)
        banner.pack(fill=X)
        banner.pack_propagate(False)
        
        banner_label = ttk.Label(banner, text="", background=color)
        banner_label.pack(fill=BOTH, expand=YES)
        
        # Title on banner
        title_frame = ttk.Frame(banner)
        title_frame.place(relx=0.05, rely=0.5, anchor=W)
        
        ttk.Label(
            title_frame,
            text=class_data.get('class_name', 'Unknown'),
            font=("Arial", 28, "bold"),
            foreground="white",
            background=color
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text=class_data.get('teacher_name', 'Teacher'),
            font=("Arial", 14),
            foreground="white",
            background=color
        ).pack(anchor=W, pady=(5, 0))
        
        # Tabs
        notebook = ttk.Notebook(self.content_frame, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Stream tab
        stream = ttk.Frame(notebook, bootstyle="dark")
        notebook.add(stream, text="Stream")
        self._build_stream_tab(stream, class_data)
        
        # Classwork tab
        classwork = ttk.Frame(notebook, bootstyle="dark")
        notebook.add(classwork, text="Classwork")
        
        # People tab
        people = ttk.Frame(notebook, bootstyle="dark")
        notebook.add(people, text="People")
    
    def _build_stream_tab(self, parent, class_data):
        """Build stream tab content"""
        ttk.Label(
            parent,
            text="📢 Announcements will appear here",
            font=("Arial", 14),
            bootstyle="inverse-secondary"
        ).pack(pady=50)
    
    def _join_class_dialog(self):
        """Show join class dialog"""
        class_code = simpledialog.askstring(
            "Join Class",
            "Enter class code:",
            parent=self.window
        )
        
        if class_code:
            self.client.join_class(class_code.strip())
    
    def _handle_server_message(self, message: dict):
        """Handle messages from server"""
        msg_type = message.get("type", "")
        
        if msg_type == "SUCCESS":
            # View classes response
            if "classes" in message:
                self.classes = message.get("classes", [])
                self._update_sidebar_classes()
                if self.current_view == "home":
                    self._show_home_page()
            
            # Join class response
            elif message.get("message", "").startswith("Successfully joined"):
                messagebox.showinfo("Success", message.get("message"))
                self.client.view_classes()  # Refresh classes
        
        elif msg_type == "ERROR":
            error = message.get("error", "Unknown error")
            messagebox.showerror("Error", error)
    
    def _on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.client.disconnect()
            self.window.destroy()
        """Create top navigation bar."""
        navbar = ttk.Frame(parent, bootstyle="primary")
        navbar.pack(fill=X, side=TOP)
        
        # Logo and title
        title_frame = ttk.Frame(navbar)
        title_frame.pack(side=LEFT, padx=20, pady=10)
        
        logo_label = ttk.Label(
            title_frame,
            text="🎓 LearnLive",
            font=("Arial", 18, "bold"),
            bootstyle="inverse-primary"
        )
        logo_label.pack(side=LEFT)
        
        # User info and actions
        user_frame = ttk.Frame(navbar)
        user_frame.pack(side=RIGHT, padx=20, pady=10)
        
        user_label = ttk.Label(
            user_frame,
            text=f"👨‍🎓 {self.user_data.get('name', 'Student')}",
            font=("Arial", 12),
            bootstyle="inverse-primary"
        )
        user_label.pack(side=LEFT, padx=(0, 15))
        
        logout_btn = ttk.Button(
            user_frame,
            text="Logout",
            command=self._handle_logout,
            bootstyle="danger-outline",
            width=10
        )
        logout_btn.pack(side=LEFT)
    
    def _create_sidebar(self, parent):
        """Create left sidebar with class list."""
        sidebar = ttk.Frame(parent, width=300, bootstyle="secondary")
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)
        
        # Sidebar header
        header_frame = ttk.Frame(sidebar, padding=15)
        header_frame.pack(fill=X)
        
        header_label = ttk.Label(
            header_frame,
            text="My Classes",
            font=("Arial", 16, "bold")
        )
        header_label.pack(anchor=W)
        
        # Join class button
        join_btn = ttk.Button(
            header_frame,
            text="➕ Join Class",
            command=self._show_join_class_dialog,
            bootstyle="success",
            width=20
        )
        join_btn.pack(pady=(10, 0))
        
        # Class list
        list_frame = ttk.Frame(sidebar)
        list_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Scrollable class list
        self.class_listbox = ttk.Treeview(
            list_frame,
            columns=("class",),
            show="tree",
            selectmode="browse",
            height=20
        )
        self.class_listbox.pack(fill=BOTH, expand=YES)
        self.class_listbox.bind("<<TreeviewSelect>>", self._on_class_selected)
        
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=VERTICAL,
            command=self.class_listbox.yview
        )
        self.class_listbox.configure(yscrollcommand=scrollbar.set)
    
    def _show_welcome_screen(self):
        """Show welcome screen."""
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        welcome_frame = ttk.Frame(self.content_area)
        welcome_frame.pack(expand=YES)
        
        welcome_label = ttk.Label(
            welcome_frame,
            text=f"Welcome, {self.user_data.get('name', 'Student')}! 👋",
            font=("Arial", 24, "bold"),
            bootstyle="primary"
        )
        welcome_label.pack(pady=20)
        
        info_label = ttk.Label(
            welcome_frame,
            text="Join a class using the class code to get started",
            font=("Arial", 14),
            bootstyle="secondary"
        )
        info_label.pack()
        
        # Quick join button
        ttk.Button(
            welcome_frame,
            text="Join Class",
            command=self._show_join_class_dialog,
            bootstyle="success",
            width=20
        ).pack(pady=20)
    
    def _show_join_class_dialog(self):
        """Show dialog to join class with code."""
        dialog = ttk.Toplevel(self.window)
        dialog.title("Join Class")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(
            form_frame,
            text="Enter Class Code",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            form_frame,
            text="Ask your teacher for the class code",
            font=("Arial", 10),
            bootstyle="secondary"
        ).pack(pady=(0, 15))
        
        # Class code entry
        code_entry = ttk.Entry(
            form_frame,
            font=("Arial", 16, "bold"),
            width=15,
            justify=CENTER
        )
        code_entry.pack(pady=(0, 20))
        code_entry.focus()
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_join():
            class_code = code_entry.get().strip()
            
            if not class_code:
                messagebox.showerror("Error", "Please enter class code")
                return
            
            self.client.join_class(class_code)
            dialog.destroy()
        
        ttk.Button(
            btn_frame,
            text="Join",
            command=handle_join,
            bootstyle="success",
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side=LEFT, padx=5)
        
        # Bind Enter key
        code_entry.bind("<Return>", lambda e: handle_join())
    
    def _on_class_selected(self, event):
        """Handle class selection from sidebar."""
        selection = self.class_listbox.selection()
        if not selection:
            return
        
        item = selection[0]
        class_id = self.class_listbox.item(item)["tags"][0] if self.class_listbox.item(item)["tags"] else None
        
        if class_id:
            # Find class data
            for cls in self.classes:
                if str(cls["_id"]) == class_id:
                    self.selected_class = cls
                    self._show_class_view()
                    break
    
    def _show_class_view(self):
        """Show detailed class view."""
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        if not self.selected_class:
            return
        
        # Class header
        header_frame = ttk.Frame(self.content_area)
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text=self.selected_class.get("class_name", "Class"),
            font=("Arial", 22, "bold"),
            bootstyle="primary"
        ).pack(anchor=W)
        
        ttk.Label(
            header_frame,
            text=f"📚 {self.selected_class.get('subject', '')} | Teacher: {self.selected_class.get('teacher_name', 'Unknown')}",
            font=("Arial", 12),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(5, 0))
        
        # Tabs for different sections
        notebook = ttk.Notebook(self.content_area, bootstyle="primary")
        notebook.pack(fill=BOTH, expand=YES)
        
        # Stream tab
        stream_frame = ttk.Frame(notebook, padding=20)
        notebook.add(stream_frame, text="Stream")
        self._create_stream_tab(stream_frame)
        
        # Assignments tab
        assignments_frame = ttk.Frame(notebook, padding=20)
        notebook.add(assignments_frame, text="Assignments")
        self._create_assignments_tab(assignments_frame)
        
        # Materials tab
        materials_frame = ttk.Frame(notebook, padding=20)
        notebook.add(materials_frame, text="Materials")
        self._create_materials_tab(materials_frame)
        
        # Classmates tab
        classmates_frame = ttk.Frame(notebook, padding=20)
        notebook.add(classmates_frame, text="Classmates")
        self._create_classmates_tab(classmates_frame)
    
    def _create_stream_tab(self, parent):
        """Create stream/announcements tab."""
        # Announcements list
        self.announcements_frame = ttk.Frame(parent)
        self.announcements_frame.pack(fill=BOTH, expand=YES)
        
        # Load announcements
        self.client.view_announcements(str(self.selected_class["_id"]))
    
    def _create_assignments_tab(self, parent):
        """Create assignments tab."""
        # Filter buttons
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(
            filter_frame,
            text="Filter:",
            font=("Arial", 11)
        ).pack(side=LEFT, padx=(0, 10))
        
        self.assignment_filter = ttk.StringVar(value="all")
        
        ttk.Radiobutton(
            filter_frame,
            text="All",
            variable=self.assignment_filter,
            value="all",
            bootstyle="primary-toolbutton"
        ).pack(side=LEFT, padx=5)
        
        ttk.Radiobutton(
            filter_frame,
            text="To Do",
            variable=self.assignment_filter,
            value="todo",
            bootstyle="primary-toolbutton"
        ).pack(side=LEFT, padx=5)
        
        ttk.Radiobutton(
            filter_frame,
            text="Submitted",
            variable=self.assignment_filter,
            value="submitted",
            bootstyle="primary-toolbutton"
        ).pack(side=LEFT, padx=5)
        
        # Assignments list
        self.assignments_frame = ttk.Frame(parent)
        self.assignments_frame.pack(fill=BOTH, expand=YES)
        
        # Load assignments
        self.client.view_assignments(str(self.selected_class["_id"]))
    
    def _create_materials_tab(self, parent):
        """Create materials tab."""
        # Materials list
        self.materials_frame = ttk.Frame(parent)
        self.materials_frame.pack(fill=BOTH, expand=YES)
        
        # Load materials
        self.client.view_materials(str(self.selected_class["_id"]))
    
    def _create_classmates_tab(self, parent):
        """Create classmates tab."""
        # Classmate count
        self.classmates_count_label = ttk.Label(
            parent,
            text="Loading classmates...",
            font=("Arial", 12),
            bootstyle="secondary"
        )
        self.classmates_count_label.pack(anchor=W, pady=(0, 20))
        
        # Classmates list
        self.classmates_listbox = ttk.Treeview(
            parent,
            columns=("name", "email"),
            show="headings",
            height=15
        )
        self.classmates_listbox.heading("name", text="Name")
        self.classmates_listbox.heading("email", text="Email")
        self.classmates_listbox.column("name", width=250)
        self.classmates_listbox.column("email", width=300)
        self.classmates_listbox.pack(fill=BOTH, expand=YES)
        
        # Load classmates
        self.client.view_students(str(self.selected_class["_id"]))
    
    def _handle_server_message(self, message: dict):
        """Handle messages from server."""
        msg_type = message.get("type", "")
        
        if msg_type == "SUCCESS":
            data = message.get("data", {})
            
            # Handle different response types
            if "classes" in data:
                self.classes = data["classes"]
                self._update_class_list()
            
            elif "announcements" in data:
                self._display_announcements(data["announcements"])
            
            elif "assignments" in data:
                self._display_assignments(data["assignments"])
            
            elif "materials" in data:
                self._display_materials(data["materials"])
            
            elif "students" in data:
                self._display_classmates(data["students"])
            
            # Show success message for actions
            action_msg = message.get("message", "")
            if action_msg and action_msg not in ["Success", "OK"]:
                messagebox.showinfo("Success", action_msg)
                
                # Refresh current view
                if "class" in action_msg.lower():
                    self.client.view_classes()
                elif self.selected_class:
                    if "assignment" in action_msg.lower():
                        self.client.view_assignments(str(self.selected_class["_id"]))
        
        elif msg_type == "ERROR":
            messagebox.showerror("Error", message.get("error", "Unknown error"))
        
        elif msg_type == "NOTIFICATION":
            # Show notification
            notification_text = message.get("message", "New notification")
            messagebox.showinfo("Notification", notification_text)
    
    def _update_class_list(self):
        """Update sidebar class list."""
        self.class_listbox.delete(*self.class_listbox.get_children())
        
        for cls in self.classes:
            class_id = str(cls["_id"])
            class_name = cls.get("class_name", "Unnamed Class")
            
            self.class_listbox.insert(
                "",
                END,
                text=f"📚 {class_name}",
                tags=(class_id,)
            )
    
    def _display_announcements(self, announcements: list):
        """Display announcements in stream tab."""
        for widget in self.announcements_frame.winfo_children():
            widget.destroy()
        
        if not announcements:
            ttk.Label(
                self.announcements_frame,
                text="No announcements yet",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack(pady=20)
            return
        
        for announcement in announcements:
            self._create_announcement_card(self.announcements_frame, announcement)
    
    def _create_announcement_card(self, parent, announcement: dict):
        """Create announcement card widget."""
        card = ttk.Frame(parent, bootstyle="light", relief="solid", borderwidth=1)
        card.pack(fill=X, pady=(0, 15))
        
        inner = ttk.Frame(card, padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(
            inner,
            text=announcement.get("title", "Announcement"),
            font=("Arial", 14, "bold")
        ).pack(anchor=W)
        
        # Metadata
        teacher_name = announcement.get("teacher_name", "Teacher")
        created_at = announcement.get("created_at", "")
        ttk.Label(
            inner,
            text=f"Posted by {teacher_name} on {created_at}",
            font=("Arial", 10),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(2, 10))
        
        # Content
        ttk.Label(
            inner,
            text=announcement.get("content", ""),
            font=("Arial", 11),
            wraplength=700
        ).pack(anchor=W, pady=(0, 10))
        
        # Actions
        action_frame = ttk.Frame(inner)
        action_frame.pack(anchor=W)
        
        ttk.Button(
            action_frame,
            text="💬 View Comments",
            command=lambda: self._view_comments(announcement),
            bootstyle="link"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            action_frame,
            text="➕ Add Comment",
            command=lambda: self._show_add_comment_dialog(announcement),
            bootstyle="link"
        ).pack(side=LEFT)
    
    def _display_assignments(self, assignments: list):
        """Display assignments."""
        for widget in self.assignments_frame.winfo_children():
            widget.destroy()
        
        if not assignments:
            ttk.Label(
                self.assignments_frame,
                text="No assignments yet",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack(pady=20)
            return
        
        # Filter assignments based on selection
        filter_val = self.assignment_filter.get()
        
        for assignment in assignments:
            # TODO: Check if submitted (need submission status from server)
            submitted = False  # assignment.get("submitted", False)
            
            if filter_val == "todo" and submitted:
                continue
            elif filter_val == "submitted" and not submitted:
                continue
            
            self._create_assignment_card(self.assignments_frame, assignment, submitted)
    
    def _create_assignment_card(self, parent, assignment: dict, submitted: bool):
        """Create assignment card widget."""
        bootstyle = "success" if submitted else "warning"
        
        card = ttk.Frame(parent, bootstyle=bootstyle, relief="solid", borderwidth=1)
        card.pack(fill=X, pady=(0, 15))
        
        inner = ttk.Frame(card, padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        # Title and status
        header = ttk.Frame(inner)
        header.pack(fill=X)
        
        ttk.Label(
            header,
            text=assignment.get("title", "Assignment"),
            font=("Arial", 14, "bold")
        ).pack(side=LEFT)
        
        status_text = "✓ Submitted" if submitted else "📝 To Do"
        status_style = "success" if submitted else "warning"
        
        ttk.Label(
            header,
            text=status_text,
            font=("Arial", 11, "bold"),
            bootstyle=status_style
        ).pack(side=RIGHT)
        
        # Points and due date
        meta_frame = ttk.Frame(inner)
        meta_frame.pack(fill=X, pady=(5, 10))
        
        ttk.Label(
            meta_frame,
            text=f"{assignment.get('max_points', 0)} points",
            font=("Arial", 10),
            bootstyle="secondary"
        ).pack(side=LEFT, padx=(0, 15))
        
        ttk.Label(
            meta_frame,
            text=f"Due: {assignment.get('due_date', 'N/A')}",
            font=("Arial", 10),
            bootstyle="secondary"
        ).pack(side=LEFT)
        
        # Description
        ttk.Label(
            inner,
            text=assignment.get("description", ""),
            font=("Arial", 11),
            wraplength=700
        ).pack(anchor=W, pady=(0, 10))
        
        # Action button
        if not submitted:
            ttk.Button(
                inner,
                text="Submit Assignment",
                command=lambda: self._show_submit_assignment_dialog(assignment),
                bootstyle="success",
                width=20
            ).pack(anchor=W)
        else:
            ttk.Button(
                inner,
                text="View Submission",
                command=lambda: self._view_submission(assignment),
                bootstyle="info-outline",
                width=20
            ).pack(anchor=W)
    
    def _display_materials(self, materials: list):
        """Display materials."""
        for widget in self.materials_frame.winfo_children():
            widget.destroy()
        
        if not materials:
            ttk.Label(
                self.materials_frame,
                text="No materials available yet",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack(pady=20)
            return
        
        # Create list of materials
        for material in materials:
            self._create_material_row(self.materials_frame, material)
    
    def _create_material_row(self, parent, material: dict):
        """Create material row widget."""
        row = ttk.Frame(parent, bootstyle="light", relief="solid", borderwidth=1)
        row.pack(fill=X, pady=(0, 10))
        
        inner = ttk.Frame(row, padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        # Icon based on type
        mat_type = material.get("material_type", "document")
        icon = "📄" if mat_type == "document" else "🖼️" if mat_type == "image" else "📕" if mat_type == "pdf" else "📎"
        
        # Left side - name and info
        left_frame = ttk.Frame(inner)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        ttk.Label(
            left_frame,
            text=f"{icon} {material.get('material_name', 'Material')}",
            font=("Arial", 13, "bold")
        ).pack(anchor=W)
        
        ttk.Label(
            left_frame,
            text=f"Type: {mat_type.title()} | Uploaded: {material.get('uploaded_at', '')}",
            font=("Arial", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(2, 0))
        
        # Right side - download button
        ttk.Button(
            inner,
            text="⬇️ Download",
            command=lambda: self._download_material(material),
            bootstyle="info-outline",
            width=15
        ).pack(side=RIGHT)
    
    def _display_classmates(self, classmates: list):
        """Display classmates list."""
        self.classmates_listbox.delete(*self.classmates_listbox.get_children())
        
        # Filter out teacher and self
        students = [s for s in classmates if s.get("_id") != self.user_data.get("_id")]
        
        self.classmates_count_label.config(text=f"Total Classmates: {len(students)}")
        
        for student in students:
            name = student.get("name", "Unknown")
            email = student.get("email", "")
            
            self.classmates_listbox.insert(
                "",
                END,
                values=(name, email)
            )
    
    def _show_add_comment_dialog(self, announcement: dict):
        """Show dialog to add comment."""
        dialog = ttk.Toplevel(self.window)
        dialog.title("Add Comment")
        dialog.geometry("500x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(
            form_frame,
            text="Write your comment:",
            font=("Arial", 11)
        ).pack(anchor=W, pady=(0, 10))
        
        comment_text = ttk.Text(form_frame, height=8, font=("Arial", 11))
        comment_text.pack(fill=BOTH, expand=YES, pady=(0, 20))
        comment_text.focus()
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_post():
            comment = comment_text.get("1.0", END).strip()
            
            if not comment:
                messagebox.showerror("Error", "Please enter a comment")
                return
            
            self.client.post_comment(str(announcement["_id"]), comment)
            dialog.destroy()
        
        ttk.Button(
            btn_frame,
            text="Post",
            command=handle_post,
            bootstyle="primary",
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side=LEFT, padx=5)
    
    def _show_submit_assignment_dialog(self, assignment: dict):
        """Show dialog to submit assignment."""
        dialog = ttk.Toplevel(self.window)
        dialog.title(f"Submit: {assignment.get('title', 'Assignment')}")
        dialog.geometry("600x450")
        dialog.transient(self.window)
        dialog.grab_set()
        
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        # Assignment info
        info_frame = ttk.Frame(form_frame, bootstyle="info", relief="solid", borderwidth=1)
        info_frame.pack(fill=X, pady=(0, 20))
        
        info_inner = ttk.Frame(info_frame, padding=10)
        info_inner.pack(fill=X)
        
        ttk.Label(
            info_inner,
            text=f"Due: {assignment.get('due_date', 'N/A')} | Points: {assignment.get('max_points', 0)}",
            font=("Arial", 10),
            bootstyle="info"
        ).pack()
        
        # Submission text
        ttk.Label(
            form_frame,
            text="Your Answer:",
            font=("Arial", 11)
        ).pack(anchor=W, pady=(0, 5))
        
        answer_text = ttk.Text(form_frame, height=10, font=("Arial", 11))
        answer_text.pack(fill=BOTH, expand=YES, pady=(0, 15))
        answer_text.focus()
        
        # File attachment
        file_frame = ttk.Frame(form_frame)
        file_frame.pack(fill=X, pady=(0, 20))
        
        file_path_var = ttk.StringVar(value="No file selected")
        
        ttk.Label(
            file_frame,
            text="Attach File (optional):",
            font=("Arial", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        file_label = ttk.Label(
            file_frame,
            textvariable=file_path_var,
            font=("Arial", 9),
            bootstyle="secondary"
        )
        file_label.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        def choose_file():
            file_path = filedialog.askopenfilename(
                title="Select File",
                filetypes=[("All Files", "*.*")]
            )
            if file_path:
                file_path_var.set(os.path.basename(file_path))
                file_path_var.file_full_path = file_path
        
        ttk.Button(
            file_frame,
            text="Choose File",
            command=choose_file,
            bootstyle="secondary-outline",
            width=15
        ).pack(side=LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_submit():
            answer = answer_text.get("1.0", END).strip()
            
            if not answer:
                messagebox.showerror("Error", "Please provide an answer")
                return
            
            file_path = getattr(file_path_var, 'file_full_path', None)
            
            self.client.submit_assignment(
                str(assignment["_id"]),
                answer,
                file_path
            )
            dialog.destroy()
        
        ttk.Button(
            btn_frame,
            text="Submit",
            command=handle_submit,
            bootstyle="success",
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side=LEFT, padx=5)
    
    def _view_comments(self, announcement: dict):
        """View comments on announcement."""
        self.client.view_comments(str(announcement["_id"]))
        # TODO: Show comments in dialog
        messagebox.showinfo("Comments", "Loading comments...")
    
    def _view_submission(self, assignment: dict):
        """View own submission."""
        # TODO: Implement view submission
        messagebox.showinfo("Submission", "Viewing your submission...")
    
    def _download_material(self, material: dict):
        """Download material file."""
        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            defaultextension=".*",
            initialfile=material.get("material_name", "material"),
            title="Save Material"
        )
        
        if save_path:
            self.client.download_file(str(material["_id"]), save_path)
            messagebox.showinfo("Download", "Downloading material...")
    
    def _handle_logout(self):
        """Handle logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.client.disconnect()
            self.window.destroy()
    
    def _on_closing(self):
        """Handle window close."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.client.disconnect()
            self.window.destroy()
