import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Canvas, simpledialog, Toplevel, Text, StringVar
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import LearnLiveClient


class TeacherDashboard:
    """Teacher Dashboard - Google Classroom Style"""
    
    def __init__(self, client: LearnLiveClient, user_data: dict):
        self.client = client
        self.user_data = user_data
        self.window = None
        self.classes = []
        self.selected_class = None
        self.current_view = "home"
        self.sidebar = None
        self.content_frame = None
        self.home_btn = None
        self.classes_frame = None
        self.search_query = ""
        self.announcements = []
        self.announcements_cache = {}  # Cache announcements by class_id
        self.last_refresh_time = {}  # Track last refresh time per class
        self.upload_dialog = None  # Track upload material dialog
        self.materials = []  # Track class materials
        self.materials_container = None  # Reference to materials display container
        self.assignments = []  # Track class assignments
        self.assignments_container = None  # Reference to assignments display container
        self.submissions_dialog = None  # Track submissions dialog
        self.pending_submissions = []  # Store submissions data
        
        self.client.set_message_callback(self._handle_server_message)
    
    def show(self):
        """Show dashboard"""
        self.window = ttk.Window(themename="darkly")
        self.window.title(f"LearnLive - {self.user_data.get('name', 'Teacher')}")
        self.window.geometry("1400x900")
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=BOTH, expand=YES)
        
        # Sidebar with white border on right
        from tkinter import Frame
        sidebar_container = Frame(main_container, bg='white', width=282)
        sidebar_container.pack(side=LEFT, fill=Y)
        sidebar_container.pack_propagate(False)
        
        self.sidebar = self._create_sidebar(sidebar_container)
        self.sidebar.pack(side=LEFT, fill=Y, padx=(0, 2))
        
        # Right container
        right_container = ttk.Frame(main_container)
        right_container.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # Header
        self._create_header(right_container).pack(side=TOP, fill=X)
        
        # Content
        self.content_frame = ttk.Frame(right_container)
        self.content_frame.pack(side=TOP, fill=BOTH, expand=YES)
        
        # Load and show
        self.client.view_classes()
        self._show_home_page()
        
        self.window.mainloop()
    
    def _create_sidebar(self, parent):
        """Create sidebar"""
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
        
        ttk.Button(nav_frame, text="✓  To-Get", command=self._show_toget_page, bootstyle="dark", width=25).pack(fill=X, pady=2)
        
        ttk.Separator(sidebar, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Classes
        ttk.Label(
            sidebar,
            text="Created Classes",
            font=("Arial", 11, "bold"),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=20, pady=(10, 5))
        
        self.classes_frame = ttk.Frame(sidebar, style="dark")
        self.classes_frame.pack(fill=BOTH, expand=YES, padx=10)
        
        # Logout button at bottom
        logout_frame = ttk.Frame(sidebar, style="dark")
        logout_frame.pack(side=BOTTOM, fill=X, padx=10, pady=20)
        
        ttk.Button(
            logout_frame,
            text="🚪  Log Out",
            command=self._logout,
            bootstyle="danger",
            width=25
        ).pack(fill=X)
        
        return sidebar
    
    def _update_sidebar_classes(self):
        """Update classes in sidebar"""
        for widget in self.classes_frame.winfo_children():
            widget.destroy()
        
        if not self.classes:
            ttk.Label(
                self.classes_frame,
                text="No classes yet",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(pady=10)
            return
        
        filtered_classes = self._filter_classes()
        for cls in filtered_classes:
            btn = ttk.Button(
                self.classes_frame,
                text=cls.get("class_name", "Unknown"),
                command=lambda c=cls: self._select_class(c),
                bootstyle="dark",
                width=25
            )
            btn.pack(fill=X, pady=2)
    
    def _create_header(self, parent):
        """Create header"""
        header = ttk.Frame(parent, bootstyle="dark")
        
        # Search
        search_frame = ttk.Frame(header, bootstyle="dark")
        search_frame.pack(side=LEFT, fill=X, expand=YES, padx=20, pady=15)
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 12), width=50)
        self.search_entry.insert(0, "🔍 Search classes...")
        self.search_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # Bind search events
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        
        # User
        user_frame = ttk.Frame(header, bootstyle="dark")
        user_frame.pack(side=RIGHT, padx=20)
        
        ttk.Button(
            user_frame,
            text="+ Create Class",
            bootstyle="success",
            command=self._create_class_dialog
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            user_frame,
            text=f"👨‍🏫 {self.user_data.get('name', 'Teacher')}",
            bootstyle="secondary-outline",
        ).pack(side=LEFT, padx=5)
        
        return header
    
    def _show_toget_page(self):
        """Show To-Get page with all student submissions"""
        self.current_view = "toget"
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if self.home_btn:
            self.home_btn.configure(bootstyle="dark")
        
        # Title
        title_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        title_frame.pack(fill=X, padx=30, pady=20)
        
        ttk.Label(
            title_frame,
            text="✓ To-Get - All Submissions",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text="View and download all student submissions",
            font=("Arial", 12),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(5, 0))
        
        # Loading message
        ttk.Label(
            self.content_frame,
            text="📥 Loading submissions...",
            font=("Arial", 14),
            bootstyle="secondary"
        ).pack(pady=50)
        
        # Request submissions (response will come via callback)
        self.client.send_message('GET_TEACHER_SUBMISSIONS', {})
    
    def _display_submissions(self, submissions):
        """Display submissions in To-Get page"""
        if self.current_view != "toget":
            return
        
        # Clear loading message
        for widget in self.content_frame.winfo_children():
            if widget.winfo_class() == 'TLabel' and 'Loading' in str(widget.cget('text')):
                widget.destroy()
        
        if not submissions:
            ttk.Label(
                self.content_frame,
                text="📭 No submissions yet",
                font=("Arial", 16),
                bootstyle="secondary"
            ).pack(pady=50)
            ttk.Label(
                self.content_frame,
                text="Student submissions will appear here",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack()
            return
        
        # Canvas for scrolling
        canvas = Canvas(self.content_frame, bg='#222222', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Submissions list
        list_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
        list_frame.pack(fill=BOTH, expand=YES, padx=30, pady=10)
        
        for submission in submissions:
            self._create_submission_card(list_frame, submission).pack(fill=X, pady=8)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _create_submission_card(self, parent, submission):
        """Create a submission card"""
        card = ttk.Frame(parent, bootstyle="secondary", relief=SOLID, borderwidth=1)
        card.pack(fill=X, pady=5)
        
        content = ttk.Frame(card, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=20, pady=15)
        
        # Header row
        header = ttk.Frame(content, bootstyle="secondary")
        header.pack(fill=X)
        
        ttk.Label(
            header,
            text=f"📝 {submission.get('assignment_title', 'Assignment')}",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT)
        
        ttk.Label(
            header,
            text=f"Class: {submission.get('class_name', 'Unknown')}",
            font=("Arial", 11),
            bootstyle="secondary"
        ).pack(side=RIGHT)
        
        # Student info
        info_frame = ttk.Frame(content, bootstyle="secondary")
        info_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Label(
            info_frame,
            text=f"👤 Student: {submission.get('student_name', 'Unknown')}",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT)
        
        ttk.Label(
            info_frame,
            text=f"📅 Submitted: {submission.get('submitted_at', 'N/A')}",
            font=("Arial", 11),
            bootstyle="secondary"
        ).pack(side=RIGHT)
        
        # File info and download button
        if submission.get('file_path'):
            file_frame = ttk.Frame(content, bootstyle="secondary")
            file_frame.pack(fill=X, pady=(10, 0))
            
            filename = os.path.basename(submission.get('file_path', ''))
            ttk.Label(
                file_frame,
                text=f"📎 {filename}",
                font=("Arial", 11),
                bootstyle="info"
            ).pack(side=LEFT)
            
            ttk.Button(
                file_frame,
                text="⬇ Download",
                command=lambda s=submission: self._download_submission(s),
                bootstyle="success-outline",
                width=15
            ).pack(side=RIGHT)
        
        return card
    
    def _download_submission(self, submission):
        """Download a submission file"""
        from tkinter import filedialog
        
        file_path = submission.get('file_path')
        if not file_path:
            messagebox.showerror("Error", "No file attached to this submission")
            return
        
        # Ask where to save
        filename = os.path.basename(file_path)
        save_path = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(filename)[1],
            initialfile=filename,
            title="Save Submission As"
        )
        
        if not save_path:
            return
        
        # Store save path for when response arrives
        self.pending_download = {
            'save_path': save_path,
            'file_path': file_path
        }
        
        # Request file download from server (response will come via callback)
        self.client.send_message('DOWNLOAD_FILE', {
            'file_path': file_path
        })
    
    def _show_home_page(self):
        """Show home page"""
        self.current_view = "home"
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        title_frame.pack(fill=X, padx=30, pady=20)
        
        ttk.Label(
            title_frame,
            text="My Classroom",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W)
        
        if not self.classes:
            self._show_empty_state()
            return
        
        # Canvas for scrolling
        canvas = Canvas(self.content_frame, bg='#222222', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Class cards grid
        cards_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
        cards_frame.pack(fill=BOTH, expand=YES, padx=30, pady=10)
        
        colors = ["#1e88e5", "#43a047", "#e53935", "#fb8c00", "#8e24aa", "#00acc1"]
        
        filtered_classes = self._filter_classes()
        for i, cls in enumerate(filtered_classes):
            row = i // 3
            col = i % 3
            
            card = self._create_class_card(cards_frame, cls, colors[i % len(colors)])
            card.grid(row=row, column=col, padx=15, pady=15, sticky=NSEW)
        
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1, minsize=300)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _create_class_card(self, parent, cls, color):
        """Create class card"""
        card = ttk.Frame(parent, bootstyle="dark")
        
        # Color banner
        banner = Canvas(card, height=80, bg=color, highlightthickness=0)
        banner.pack(fill=X)
        
        banner.create_text(
            15, 15,
            text=cls.get("class_name", "Unknown"),
            anchor=NW,
            fill="white",
            font=("Arial", 16, "bold")
        )
        
        banner.create_text(
            15, 45,
            text=cls.get("subject", ""),
            anchor=NW,
            fill="white",
            font=("Arial", 11)
        )
        
        # Content
        content = ttk.Frame(card, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=2, pady=2)
        
        # Section
        section = cls.get('section', '')
        if section:
            ttk.Label(
                content,
                text=f"📋 Section: {section}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, padx=15, pady=(15, 5))
        
        # Room
        room = cls.get('room', '')
        if room:
            ttk.Label(
                content,
                text=f"🚪 Room: {room}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, padx=15, pady=(0, 5))
        
        ttk.Label(
            content,
            text=f"Class Code: {cls.get('class_code', 'N/A')}",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=15, pady=(0, 5))
        
        ttk.Label(
            content,
            text=f"Students: {len(cls.get('students', []))}",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=15, pady=(0, 15))
        
        # Click handler
        card.bind("<Button-1>", lambda e, c=cls: self._select_class(c))
        banner.bind("<Button-1>", lambda e, c=cls: self._select_class(c))
        
        return card
    
    def _show_empty_state(self):
        """Show empty state"""
        empty_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        empty_frame.pack(expand=YES)
        
        ttk.Label(
            empty_frame,
            text="📚",
            font=("Arial", 60)
        ).pack()
        
        ttk.Label(
            empty_frame,
            text="No classes created yet",
            font=("Arial", 18, "bold"),
            bootstyle="inverse-light"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            empty_frame,
            text="Create your first class to get started",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        ).pack(pady=(0, 20))
        
        ttk.Button(
            empty_frame,
            text="+ Create Class",
            bootstyle="success",
            command=self._create_class_dialog,
            width=20
        ).pack()
    
    def _select_class(self, cls):
        """Select and show class"""
        self.selected_class = cls
        self._show_class_page()
    
    def _show_class_page(self):
        """Show class detail page"""
        self.current_view = "class"
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_class:
            return
        
        # Class header
        header = ttk.Frame(self.content_frame, bootstyle="primary", height=100)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        ttk.Label(
            header,
            text=self.selected_class.get("class_name", "Unknown"),
            font=("Arial", 20, "bold"),
            bootstyle="inverse-primary"
        ).pack(anchor=W, padx=30, pady=(20, 5))
        
        ttk.Label(
            header,
            text=self.selected_class.get("subject", ""),
            font=("Arial", 12),
            bootstyle="inverse-primary"
        ).pack(anchor=W, padx=30)
        
        # Tabs
        notebook = ttk.Notebook(self.content_frame, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Announcements tab
        stream_frame = ttk.Frame(notebook, bootstyle="dark")
        self._create_stream_tab(stream_frame)
        notebook.add(stream_frame, text="Announcements")
        
        # Assignments tab
        assignments_frame = ttk.Frame(notebook, bootstyle="dark")
        self._create_assignments_tab(assignments_frame)
        notebook.add(assignments_frame, text="Assignments")
        
        # Class Materials tab
        materials_frame = ttk.Frame(notebook, bootstyle="dark")
        self._create_materials_tab(materials_frame)
        notebook.add(materials_frame, text="Class Materials")
        
        # People tab
        people_frame = ttk.Frame(notebook, bootstyle="dark")
        self._create_people_tab(people_frame)
        notebook.add(people_frame, text="People")
    
    def _create_stream_tab(self, parent):
        """Create announcements tab"""
        ttk.Label(
            parent,
            text="Class Announcements",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=20)
        
        ttk.Button(
            parent,
            text="📢 Post Announcement",
            bootstyle="primary",
            command=self._post_announcement_dialog
        ).pack(anchor=W, padx=20, pady=(0, 20))
        
        # Load announcements for this class (check cache first)
        if self.selected_class:
            class_id = self.selected_class["_id"]
            
            # Check if we have recent cached data (within 10 seconds)
            import time
            current_time = time.time()
            last_refresh = self.last_refresh_time.get(class_id, 0)
            
            if current_time - last_refresh < 10 and class_id in self.announcements_cache:
                # Use cached data
                self.announcements = self.announcements_cache[class_id]
                self._update_stream_display()
            else:
                # Fetch fresh data
                self.client.view_announcements(class_id)
                self.last_refresh_time[class_id] = current_time
        
        # Scrollable announcements area
        from tkinter import Canvas, Scrollbar
        self.stream_canvas = Canvas(parent, bg="#222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.stream_canvas.yview)
        self.stream_container = ttk.Frame(self.stream_canvas, bootstyle="dark")
        
        self.stream_container.bind("<Configure>", lambda e: self.stream_canvas.configure(scrollregion=self.stream_canvas.bbox("all")))
        self.stream_canvas_window = self.stream_canvas.create_window((0, 0), window=self.stream_container, anchor="nw")
        self.stream_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Update canvas window width when canvas is resized
        def update_canvas_width(event):
            self.stream_canvas.itemconfig(self.stream_canvas_window, width=event.width)
        self.stream_canvas.bind("<Configure>", update_canvas_width)
        
        self.stream_canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Show loading message - will be replaced when announcements arrive
        ttk.Label(
            self.stream_container,
            text="Loading announcements...",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(padx=20, pady=20)
    
    def _update_stream_display(self):
        """Update the stream display with announcements"""
        print(f"[DEBUG] _update_stream_display called, announcements count: {len(self.announcements)}")
        
        if not hasattr(self, 'stream_container'):
            print("[DEBUG] No stream_container attribute")
            return
        
        try:
            # Check if the widget still exists
            exists = self.stream_container.winfo_exists()
            print(f"[DEBUG] stream_container exists: {exists}")
        except Exception as e:
            print(f"[DEBUG] Error checking widget existence: {e}")
            return
        
        # Clear existing widgets
        for widget in self.stream_container.winfo_children():
            widget.destroy()
        
        print(f"[DEBUG] Cleared old widgets, creating new ones for {len(self.announcements)} announcements")
        
        if not self.announcements:
            ttk.Label(
                self.stream_container,
                text="No announcements yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            print("[DEBUG] Displayed 'No announcements' message")
            return
        
        # Display announcements
        for idx, announcement in enumerate(self.announcements):
            print(f"[DEBUG] Creating widget for announcement {idx}: {announcement.get('title')}")
            frame = ttk.Frame(self.stream_container, bootstyle="secondary", padding=15)
            frame.pack(fill=X, padx=20, pady=10)
            
            # Title
            ttk.Label(
                frame,
                text=announcement.get('title', 'Announcement'),
                font=("Arial", 14, "bold"),
                bootstyle="inverse-light"
            ).pack(anchor=W, pady=(0, 5))
            
            # Content
            ttk.Label(
                frame,
                text=announcement.get('content', ''),
                font=("Arial", 11),
                bootstyle="inverse-secondary",
                wraplength=700
            ).pack(anchor=W, pady=(0, 5))
            
            # Date
            date_str = announcement.get('created_at', '')
            if date_str:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%B %d, %Y at %I:%M %p')
                except:
                    formatted_date = date_str
                
                ttk.Label(
                    frame,
                    text=formatted_date,
                    font=("Arial", 9),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W)
        
        # Update canvas scroll region after adding content
        if hasattr(self, 'stream_canvas'):
            try:
                self.stream_container.update_idletasks()
                self.stream_canvas.configure(scrollregion=self.stream_canvas.bbox("all"))
            except:
                pass
    
    def _create_assignments_tab(self, parent):
        """Create assignments tab"""
        ttk.Label(
            parent,
            text="Assignments",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=20)
        
        ttk.Button(
            parent,
            text="+ Create Assignment",
            bootstyle="success",
            command=self._create_assignment_dialog
        ).pack(anchor=W, padx=20, pady=(0, 20))
        
        # Assignments container with scrollbar
        assignments_container = ttk.Frame(parent, bootstyle="dark")
        assignments_container.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        
        # Store reference for updates
        self.assignments_container = assignments_container
        
        # Fetch and display assignments
        if self.selected_class:
            self.client.view_assignments(self.selected_class['_id'])
    
    def _create_materials_tab(self, parent):
        """Create materials tab"""
        ttk.Label(
            parent,
            text="Class Materials",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=20)
        
        ttk.Button(
            parent,
            text="📎 Upload Material",
            bootstyle="info",
            command=self._upload_material_dialog
        ).pack(anchor=W, padx=20, pady=(0, 20))
        
        # Materials container with scrollbar
        materials_container = ttk.Frame(parent, bootstyle="dark")
        materials_container.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        
        # Store reference for updates
        self.materials_container = materials_container
        
        # Fetch and display materials
        if self.selected_class:
            self.client.view_materials(self.selected_class['_id'])
    
    def _display_materials(self):
        """Display materials in classwork tab"""
        if not self.materials_container:
            return
        
        # Clear existing widgets
        for widget in self.materials_container.winfo_children():
            widget.destroy()
        
        if not self.materials:
            ttk.Label(
                self.materials_container,
                text="No materials uploaded yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            return
        
        # Create scrollable frame
        from tkinter import Canvas, Scrollbar
        canvas = Canvas(self.materials_container, bg='#222222', highlightthickness=0)
        scrollbar = Scrollbar(self.materials_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Display each material
        for material in self.materials:
            material_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
            material_frame.pack(fill=X, padx=10, pady=5)
            
            # Material card
            card = ttk.Frame(material_frame, bootstyle="secondary", relief="raised")
            card.pack(fill=X, padx=5, pady=5)
            
            # Material info
            info_frame = ttk.Frame(card, bootstyle="secondary")
            info_frame.pack(fill=X, padx=15, pady=10)
            
            # Title and type
            title_text = material.get('title', 'Untitled')
            mat_type = material.get('material_type', 'Document')
            
            # Header with title and open button
            header_frame = ttk.Frame(info_frame, bootstyle="secondary")
            header_frame.pack(fill=X, anchor=W)
            
            ttk.Label(
                header_frame,
                text=f"📎 {title_text}",
                font=("Arial", 12, "bold"),
                bootstyle="inverse-secondary"
            ).pack(side=LEFT)
            
            # Open button
            file_path = material.get('file_path', '')
            if file_path:
                def open_material(path=file_path):
                    import os
                    import subprocess
                    if os.path.exists(path):
                        try:
                            # Use 'open' command on macOS to open file with default application
                            subprocess.run(['open', path])
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not open file: {str(e)}")
                    else:
                        messagebox.showerror("Error", "File not found")
                
                ttk.Button(
                    header_frame,
                    text="Open",
                    bootstyle="info-outline",
                    command=open_material,
                    width=8
                ).pack(side=RIGHT, padx=(10, 0))
            
            ttk.Label(
                info_frame,
                text=f"Type: {mat_type}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, pady=(5, 0))
            
            # File path
            if file_path:
                import os
                file_name = os.path.basename(file_path)
                ttk.Label(
                    info_frame,
                    text=f"File: {file_name}",
                    font=("Arial", 10),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(2, 0))
            
            # Upload date
            uploaded_at = material.get('uploaded_at', '')
            if uploaded_at:
                ttk.Label(
                    info_frame,
                    text=f"Uploaded: {uploaded_at}",
                    font=("Arial", 9),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(2, 0))
    
    def _display_assignments(self):
        """Display assignments in assignments tab"""
        if not self.assignments_container:
            return
        
        # Clear existing widgets
        for widget in self.assignments_container.winfo_children():
            widget.destroy()
        
        if not self.assignments:
            ttk.Label(
                self.assignments_container,
                text="No assignments created yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            return
        
        # Create scrollable frame
        from tkinter import Canvas, Scrollbar
        canvas = Canvas(self.assignments_container, bg='#222222', highlightthickness=0)
        scrollbar = Scrollbar(self.assignments_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Display each assignment
        for assignment in self.assignments:
            assignment_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
            assignment_frame.pack(fill=X, padx=10, pady=5)
            
            # Assignment card
            card = ttk.Frame(assignment_frame, bootstyle="secondary", relief="raised")
            card.pack(fill=X, padx=5, pady=5)
            
            # Assignment info
            info_frame = ttk.Frame(card, bootstyle="secondary")
            info_frame.pack(fill=X, padx=15, pady=10)
            
            # Title
            title_text = assignment.get('title', 'Untitled')
            
            ttk.Label(
                info_frame,
                text=f"📝 {title_text}",
                font=("Arial", 12, "bold"),
                bootstyle="inverse-secondary"
            ).pack(anchor=W)
            
            # Description
            description = assignment.get('description', '')
            if description:
                ttk.Label(
                    info_frame,
                    text=description[:100] + ('...' if len(description) > 100 else ''),
                    font=("Arial", 10),
                    bootstyle="inverse-secondary",
                    wraplength=600
                ).pack(anchor=W, pady=(5, 0))
            
            # Due date and points
            details_frame = ttk.Frame(info_frame, bootstyle="secondary")
            details_frame.pack(fill=X, pady=(5, 0))
            
            due_date = assignment.get('due_date', 'No due date')
            ttk.Label(
                details_frame,
                text=f"📅 Due: {due_date}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(side=LEFT, padx=(0, 20))
            
            max_points = assignment.get('max_points', 0)
            ttk.Label(
                details_frame,
                text=f"💯 Points: {max_points}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(side=LEFT)
            
            # Created date
            created_at = assignment.get('created_at', '')
            if created_at:
                ttk.Label(
                    info_frame,
                    text=f"Created: {created_at}",
                    font=("Arial", 9),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(2, 0))
            
            # View Submissions button
            def view_submissions(assignment_id=assignment.get('_id'), assignment_title=title_text):
                self._show_submissions_dialog(assignment_id, assignment_title)
            
            ttk.Button(
                info_frame,
                text="📂 View Submissions",
                command=view_submissions,
                bootstyle="info",
                width=20
            ).pack(pady=(10, 0))
    
    def _create_people_tab(self, parent):
        """Create people tab"""
        # Teacher section
        ttk.Label(
            parent,
            text="Teacher",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=(20, 10))
        
        teacher_frame = ttk.Frame(parent, bootstyle="secondary")
        teacher_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        teacher_name = self.user_data.get('name', 'Teacher')
        ttk.Label(
            teacher_frame,
            text=f"👤 {teacher_name}",
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=15, pady=10)
        
        # Students section
        ttk.Label(
            parent,
            text="Students",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=(10, 10))
        
        student_list = self.selected_class.get("student_list", [])
        
        if student_list:
            # Create scrollable frame for students
            canvas = Canvas(parent, bg="#222", highlightthickness=0, height=300)
            scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
            students_container = ttk.Frame(canvas, bootstyle="dark")
            
            students_container.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=students_container, anchor=NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=YES, padx=(20, 0))
            scrollbar.pack(side=RIGHT, fill=Y, padx=(0, 20))
            
            for student in student_list:
                student_frame = ttk.Frame(students_container, bootstyle="secondary")
                student_frame.pack(fill=X, padx=0, pady=5)
                
                ttk.Label(
                    student_frame,
                    text=f"👤 {student.get('name', 'Student')}",
                    font=("Arial", 11),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, padx=15, pady=8)
        else:
            ttk.Label(
                parent,
                text="No students enrolled yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, padx=20, pady=10)
    
    def _create_class_dialog(self):
        """Show create class dialog"""
        from tkinter import Toplevel
        
        dialog = Toplevel(self.window)
        dialog.title("Create Class")
        dialog.geometry("550x500")
        dialog.configure(bg='#222222')
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=30, bootstyle="dark")
        frame.pack(fill=BOTH, expand=YES)
        
        # Title
        title_label = ttk.Label(
            frame, 
            text="Create Class", 
            font=("Arial", 18, "bold"),
            bootstyle="inverse-light"
        )
        title_label.pack(pady=(0, 25))
        
        # Class name (required)
        name_label = ttk.Label(
            frame, 
            text="Class name (required)", 
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        name_label.pack(anchor=W, pady=(0, 5))
        name_entry = ttk.Entry(frame, font=("Arial", 12))
        name_entry.pack(fill=X, pady=(0, 20))
        name_entry.focus()
        
        # Section
        section_label = ttk.Label(
            frame, 
            text="Section", 
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        section_label.pack(anchor=W, pady=(0, 5))
        section_entry = ttk.Entry(frame, font=("Arial", 12))
        section_entry.pack(fill=X, pady=(0, 20))
        
        # Subject
        subject_label = ttk.Label(
            frame, 
            text="Subject", 
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        subject_label.pack(anchor=W, pady=(0, 5))
        subject_entry = ttk.Entry(frame, font=("Arial", 12))
        subject_entry.pack(fill=X, pady=(0, 20))
        
        # Room
        room_label = ttk.Label(
            frame, 
            text="Room", 
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        )
        room_label.pack(anchor=W, pady=(0, 5))
        room_entry = ttk.Entry(frame, font=("Arial", 12))
        room_entry.pack(fill=X, pady=(0, 30))
        
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Class name is required", parent=dialog)
                return
            
            self.client.create_class(
                name=name,
                section=section_entry.get().strip(),
                subject=subject_entry.get().strip(),
                room=room_entry.get().strip()
            )
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(frame, bootstyle="dark")
        btn_frame.pack(fill=X, pady=(10, 0))
        
        create_btn = ttk.Button(
            btn_frame, 
            text="Create", 
            bootstyle="success", 
            command=create, 
            width=15
        )
        create_btn.pack(side=RIGHT)
        
        cancel_btn = ttk.Button(
            btn_frame, 
            text="Cancel", 
            bootstyle="secondary", 
            command=dialog.destroy, 
            width=15
        )
        cancel_btn.pack(side=RIGHT, padx=(0, 10))
        
        # Bind Enter key to create
        dialog.bind('<Return>', lambda e: create())
    
    def _post_announcement_dialog(self):
        """Show post announcement dialog"""
        if not self.selected_class:
            return
        
        from tkinter import Toplevel, Text, Scrollbar
        
        # Create custom dialog
        dialog = Toplevel(self.window)
        dialog.title("Post Announcement")
        dialog.geometry("600x400")
        dialog.configure(bg='#222222')
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20, bootstyle="dark")
        frame.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(
            frame,
            text="Post Announcement",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(pady=(0, 15))
        
        # Title field
        ttk.Label(
            frame,
            text="Title:",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        title_entry = ttk.Entry(frame, font=("Arial", 12))
        title_entry.pack(fill=X, pady=(0, 15))
        title_entry.focus()
        
        # Message field
        ttk.Label(
            frame,
            text="Message:",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        # Text area with scrollbar
        text_frame = ttk.Frame(frame, bootstyle="dark", height=150)
        text_frame.pack(fill=BOTH, pady=(0, 15))
        text_frame.pack_propagate(False)
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        text_area = Text(
            text_frame,
            font=("Arial", 12),
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg='#2b2b2b',
            fg='white',
            insertbackground='white',
            relief='flat',
            padx=10,
            pady=10
        )
        text_area.pack(fill=BOTH, expand=YES)
        scrollbar.config(command=text_area.yview)
        
        result = {'posted': False}
        
        def post():
            title = title_entry.get().strip()
            content = text_area.get("1.0", "end-1c").strip()
            
            if not title:
                messagebox.showwarning("Warning", "Please enter a title", parent=dialog)
                return
            if not content:
                messagebox.showwarning("Warning", "Please enter a message", parent=dialog)
                return
            
            self.client.post_announcement(self.selected_class["_id"], title, content)
            result['posted'] = True
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(frame, bootstyle="dark")
        btn_frame.pack(fill=X, pady=(10, 0))
        
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        )
        cancel_btn.pack(side=RIGHT, padx=(10, 0))
        
        ok_btn = ttk.Button(
            btn_frame,
            text="Post",
            bootstyle="primary",
            command=post,
            width=15
        )
        ok_btn.pack(side=RIGHT)
    
    def _create_assignment_dialog(self):
        """Show create assignment dialog"""
        if not self.selected_class:
            return
        
        dialog = Toplevel(self.window)
        dialog.title("Create Assignment")
        dialog.geometry("600x550")
        dialog.configure(bg='#222222')
        
        frame = ttk.Frame(dialog, padding=20, bootstyle="dark")
        frame.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(
            frame,
            text="Create New Assignment",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-dark"
        ).pack(pady=(0, 20))
        
        # Assignment Title
        ttk.Label(frame, text="Title:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        title_entry = ttk.Entry(frame, font=("Arial", 11), width=50)
        title_entry.pack(fill=X, pady=(0, 15))
        
        # Description
        ttk.Label(frame, text="Description:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        
        desc_frame = ttk.Frame(frame, bootstyle="dark", height=150)
        desc_frame.pack(fill=BOTH, pady=(0, 15))
        desc_frame.pack_propagate(False)
        
        desc_text = Text(
            desc_frame,
            font=("Arial", 11),
            wrap="word",
            bg='#2b2b2b',
            fg='white',
            insertbackground='white',
            relief="flat"
        )
        desc_scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.pack(side=RIGHT, fill=Y)
        desc_text.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Due Date
        ttk.Label(frame, text="Due Date (YYYY-MM-DD):", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        due_date_entry = ttk.Entry(frame, font=("Arial", 11), width=50)
        due_date_entry.pack(fill=X, pady=(0, 15))
        due_date_entry.insert(0, "2025-12-31")  # Default date
        
        # Max Points
        ttk.Label(frame, text="Max Points:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        points_entry = ttk.Entry(frame, font=("Arial", 11), width=50)
        points_entry.pack(fill=X, pady=(0, 15))
        points_entry.insert(0, "100")  # Default points
        
        def create_assignment():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", "end-1c").strip()
            due_date = due_date_entry.get().strip()
            
            try:
                max_points = int(points_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Max points must be a number", parent=dialog)
                return
            
            if not title:
                messagebox.showerror("Error", "Title is required", parent=dialog)
                return
            
            if not due_date:
                messagebox.showerror("Error", "Due date is required", parent=dialog)
                return
            
            # Send to server
            self.client.create_assignment(
                self.selected_class['_id'],
                title,
                description,
                due_date,
                max_points
            )
            
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(frame, bootstyle="dark")
        btn_frame.pack(fill=X, pady=(10, 0))
        
        create_btn = ttk.Button(
            btn_frame,
            text="Create",
            bootstyle="success",
            command=create_assignment,
            width=15
        )
        create_btn.pack(side=LEFT)
        
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        )
        cancel_btn.pack(side=RIGHT)
    
    def _upload_material_dialog(self):
        """Show upload material dialog"""
        if not self.selected_class:
            return
        
        dialog = Toplevel(self.window)
        dialog.title("Upload Material")
        dialog.geometry("600x400")
        dialog.configure(bg='#222222')
        
        frame = ttk.Frame(dialog, padding=20, bootstyle="dark")
        frame.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(
            frame,
            text="Upload Class Material",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-dark"
        ).pack(pady=(0, 20))
        
        # Material Name
        ttk.Label(frame, text="Material Name:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        name_entry = ttk.Entry(frame, font=("Arial", 11), width=50)
        name_entry.pack(fill=X, pady=(0, 15))
        
        # Material Type
        ttk.Label(frame, text="Material Type:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        type_var = StringVar(value="Document")
        type_combo = ttk.Combobox(
            frame,
            textvariable=type_var,
            values=["Document", "Presentation", "Video", "Link", "Other"],
            font=("Arial", 11),
            state="readonly",
            width=48
        )
        type_combo.pack(fill=X, pady=(0, 15))
        
        # File Path
        ttk.Label(frame, text="File Path:", font=("Arial", 11), bootstyle="inverse-dark").pack(anchor=W, pady=(0, 5))
        
        file_frame = ttk.Frame(frame, bootstyle="dark")
        file_frame.pack(fill=X, pady=(0, 15))
        
        file_entry = ttk.Entry(file_frame, font=("Arial", 11))
        file_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        def browse_file():
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Select File",
                filetypes=[("All Files", "*.*")]
            )
            if filename:
                file_entry.delete(0, END)
                file_entry.insert(0, filename)
        
        ttk.Button(
            file_frame,
            text="Browse",
            bootstyle="info",
            command=browse_file
        ).pack(side=RIGHT)
        
        def upload_material():
            material_name = name_entry.get().strip()
            material_type = type_var.get()
            file_path = file_entry.get().strip()
            
            if not material_name:
                messagebox.showerror("Error", "Material name is required")
                return
            
            if not file_path:
                messagebox.showerror("Error", "File path is required")
                return
            
            # Check if file exists
            import os
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "File does not exist")
                return
            
            # Store dialog reference for response handling
            self.upload_dialog = dialog
            
            # Send to server (response will come via callback)
            self.client.upload_material(
                self.selected_class['_id'],
                material_name,
                material_type,
                file_path
            )
        
        # Buttons
        btn_frame = ttk.Frame(frame, bootstyle="dark")
        btn_frame.pack(fill=X, pady=(10, 0))
        
        upload_btn = ttk.Button(
            btn_frame,
            text="Upload",
            bootstyle="info",
            command=upload_material,
            width=15
        )
        upload_btn.pack(side=LEFT)
        
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        )
        cancel_btn.pack(side=RIGHT)
    
    def _on_search_focus_in(self, event):
        """Handle search entry focus in"""
        if self.search_entry.get() == "🔍 Search classes...":
            self.search_entry.delete(0, END)
    
    def _on_search_focus_out(self, event):
        """Handle search entry focus out"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "🔍 Search classes...")
    
    def _on_search_change(self, event):
        """Handle search query change"""
        query = self.search_entry.get()
        if query != "🔍 Search classes...":
            self.search_query = query.lower()
        else:
            self.search_query = ""
        
        # Refresh views
        self._update_sidebar_classes()
        if self.current_view == "home":
            self._show_home_page()
    
    def _filter_classes(self):
        """Filter classes based on search query"""
        if not self.search_query:
            return self.classes
        
        filtered = []
        for cls in self.classes:
            # Search in class name, subject, section, room
            if (self.search_query in cls.get('class_name', '').lower() or
                self.search_query in cls.get('subject', '').lower() or
                self.search_query in cls.get('section', '').lower() or
                self.search_query in cls.get('room', '').lower()):
                filtered.append(cls)
        return filtered
    
    def _handle_server_message(self, message):
        """Handle server messages"""
        msg_type = message.get("type")
        print(f"[DEBUG] _handle_server_message called: type={msg_type}, keys={message.keys()}")
        
        if msg_type == "SUCCESS":
            if "classes" in message:
                self.classes = message["classes"]
                self._update_sidebar_classes()
                if self.current_view == "home":
                    self._show_home_page()
            elif "announcement_id" in message:
                # Handle POST_ANNOUNCEMENT response - clear cache and reload announcements
                if self.selected_class:
                    class_id = self.selected_class["_id"]
                    # Clear cache to force fresh data
                    if class_id in self.announcements_cache:
                        del self.announcements_cache[class_id]
                    self.client.view_announcements(class_id)
            elif "assignment_id" in message:
                # Handle CREATE_ASSIGNMENT response
                messagebox.showinfo("Success", "Assignment created successfully!")
                if self.selected_class:
                    # Refresh assignments list for the class view
                    self.client.view_assignments(self.selected_class['_id'])
                # If currently viewing To-Get page, refresh all submissions
                if self.current_view == "toget":
                    print(f"[DEBUG] Refreshing To-Get page after assignment creation")
                    self.client.send_message('GET_TEACHER_SUBMISSIONS', {})
            elif "material_id" in message:
                # Handle UPLOAD_MATERIAL response
                if hasattr(self, 'upload_dialog') and self.upload_dialog:
                    self.upload_dialog.destroy()
                    self.upload_dialog = None
                messagebox.showinfo("Success", "Material uploaded successfully!")
                if self.selected_class:
                    # Refresh materials list
                    self.client.view_materials(self.selected_class['_id'])
            elif "announcements" in message:
                # Handle VIEW_ANNOUNCEMENTS response
                print(f"[DEBUG] Received announcements: count={len(message.get('announcements', []))}")
                self.announcements = message.get("announcements", [])
                print(f"[DEBUG] self.announcements set to: {len(self.announcements)} items")
                
                # Cache announcements for this class
                if self.selected_class:
                    class_id = self.selected_class["_id"]
                    self.announcements_cache[class_id] = self.announcements
                    print(f"[DEBUG] Cached announcements for class: {class_id}")
                
                print(f"[DEBUG] About to call _update_stream_display")
                # Use window.after to ensure GUI update happens in main thread
                if hasattr(self, 'window') and self.window:
                    self.window.after(0, self._update_stream_display)
                else:
                    self._update_stream_display()
                print(f"[DEBUG] _update_stream_display scheduled")
            elif "assignments" in message:
                # Handle VIEW_ASSIGNMENTS response
                self.assignments = message.get("assignments", [])
                print(f"[DEBUG] Received assignments: count={len(self.assignments)}")
                if hasattr(self, 'assignments_container') and self.assignments_container:
                    print(f"[DEBUG] assignments_container exists, calling _display_assignments")
                    try:
                        self.window.after(0, self._display_assignments)
                    except Exception as e:
                        print(f"[DEBUG] Error displaying assignments: {e}")
                else:
                    print(f"[DEBUG] assignments_container not available yet")
            elif "materials" in message:
                # Handle VIEW_MATERIALS response
                self.materials = message.get("materials", [])
                print(f"[DEBUG] Received materials: count={len(self.materials)}")
                if hasattr(self, 'materials_container') and self.materials_container:
                    print(f"[DEBUG] materials_container exists, calling _display_materials")
                    try:
                        self.window.after(0, self._display_materials)
                    except Exception as e:
                        print(f"[DEBUG] Error displaying materials: {e}")
                else:
                    print(f"[DEBUG] materials_container not available yet")
            elif "submissions" in message:
                # Handle submissions response - could be for To-Get page or dialog
                submissions = message.get("submissions", [])
                print(f"[DEBUG] Received submissions: count={len(submissions)}")
                
                # Check if this is for the To-Get page (has class_name in submissions)
                if submissions and 'class_name' in submissions[0]:
                    print(f"[DEBUG] Submissions are for To-Get page")
                    self.window.after(0, lambda: self._display_submissions(submissions))
                # Check if this is for the View Submissions dialog
                elif self.submissions_dialog and self.submissions_dialog.winfo_exists():
                    print(f"[DEBUG] Updating submissions dialog")
                    self.window.after(0, lambda: self._display_submissions_in_dialog(self.submissions_dialog, submissions))
                else:
                    print(f"[DEBUG] No active submissions dialog or To-Get page")
            elif "file_data" in message:
                # Handle DOWNLOAD_FILE response
                if hasattr(self, 'pending_download'):
                    file_data = message.get('file_data')
                    save_path = self.pending_download.get('save_path')
                    if file_data and save_path:
                        try:
                            import base64
                            with open(save_path, 'wb') as f:
                                f.write(base64.b64decode(file_data))
                            messagebox.showinfo("Success", f"File downloaded successfully!\n{save_path}")
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                    else:
                        messagebox.showerror("Error", "No file data received")
                    delattr(self, 'pending_download')
            elif message.get("message", "").startswith("Class created"):
                # Refresh classes first to show the new class immediately
                self.client.view_classes()
                # Show success message after a brief delay to allow UI update
                self.window.after(100, lambda: messagebox.showinfo("Success", message.get("message")))
        elif msg_type == "NOTIFICATION":
            # Handle real-time notifications
            notification = message.get('notification', {})
            notif_type = notification.get('type')
            
            if notif_type == 'NEW_SUBMISSION':
                # A student submitted an assignment - refresh To-Get page if active
                print(f"[DEBUG] Received NEW_SUBMISSION notification")
                if self.current_view == "toget":
                    print(f"[DEBUG] Refreshing To-Get page after new submission")
                    self.client.send_message('GET_TEACHER_SUBMISSIONS', {})
        elif msg_type == "ERROR":
            messagebox.showerror("Error", message.get("error", "Unknown error"))
    
    def _logout(self):
        """Handle logout"""
        if messagebox.askokcancel("Log Out", "Are you sure you want to log out?"):
            self.client.disconnect()
            self.window.destroy()
            
            # Show login screen again
            from client.login_gui import LoginWindow
            from client.client import LearnLiveClient
            
            # Create new client and login window
            new_client = LearnLiveClient()
            
            def on_login_success(user_data: dict):
                """Handle successful login after logout"""
                role = user_data.get("role", "student")
                if role == "teacher":
                    dashboard = TeacherDashboard(new_client, user_data)
                    dashboard.show()
                else:
                    from client.student_dashboard import StudentDashboard
                    dashboard = StudentDashboard(new_client, user_data)
                    dashboard.show()
            
            login = LoginWindow(new_client, on_login_success)
            login.show()
    
    def _show_submissions_dialog(self, assignment_id, assignment_title):
        """Show dialog with all student submissions for an assignment"""
        # Create dialog window
        dialog = ttk.Toplevel(self.window)
        dialog.title(f"Submissions - {assignment_title}")
        dialog.geometry("800x600")
        
        # Header
        ttk.Label(
            dialog,
            text=f"Student Submissions for: {assignment_title}",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-light"
        ).pack(padx=20, pady=20)
        
        # Fetch submissions from server
        print(f"[DEBUG] Calling view_submissions for assignment_id: {assignment_id}")
        self.client.view_submissions(assignment_id)
        
        # Create scrollable frame for submissions
        from tkinter import Canvas, Scrollbar
        canvas = Canvas(dialog, bg='#222222', highlightthickness=0)
        scrollbar = Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES, padx=(20, 0), pady=(0, 20))
        scrollbar.pack(side=RIGHT, fill=Y, pady=(0, 20), padx=(0, 20))
        
        # Store reference for update
        dialog.submissions_frame = scrollable_frame
        dialog.assignment_id = assignment_id
        self.submissions_dialog = dialog  # Store dialog reference for message handler
        print(f"[DEBUG] Dialog created and stored, self.submissions_dialog = {self.submissions_dialog}")
        
        # Loading message
        ttk.Label(
            scrollable_frame,
            text="Loading submissions...",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(padx=20, pady=20)
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            bootstyle="secondary",
            width=15
        ).pack(pady=(0, 20))
    
    def _display_submissions_in_dialog(self, dialog, submissions):
        """Display submissions in the dialog"""
        print(f"[DEBUG] _display_submissions_in_dialog called with {len(submissions)} submissions")
        
        if not hasattr(dialog, 'submissions_frame'):
            print(f"[DEBUG] Dialog doesn't have submissions_frame attribute")
            return
        
        # Clear existing widgets
        for widget in dialog.submissions_frame.winfo_children():
            widget.destroy()
        
        if not submissions:
            ttk.Label(
                dialog.submissions_frame,
                text="No submissions yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            return
        
        # Display each submission
        for submission in submissions:
            sub_frame = ttk.Frame(dialog.submissions_frame, bootstyle="secondary", relief="raised")
            sub_frame.pack(fill=X, padx=10, pady=5)
            
            info_frame = ttk.Frame(sub_frame, bootstyle="secondary")
            info_frame.pack(fill=X, padx=15, pady=10)
            
            # Student name
            student_name = submission.get('student_name', 'Unknown Student')
            ttk.Label(
                info_frame,
                text=f"👤 {student_name}",
                font=("Arial", 12, "bold"),
                bootstyle="inverse-secondary"
            ).pack(anchor=W)
            
            # Submitted date
            submitted_at = submission.get('submitted_at', '')
            if submitted_at:
                ttk.Label(
                    info_frame,
                    text=f"📅 Submitted: {submitted_at}",
                    font=("Arial", 10),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(5, 0))
            
            # File info and download button
            file_path = submission.get('file_path', '')
            if file_path:
                import os
                file_name = os.path.basename(file_path)
                
                file_frame = ttk.Frame(info_frame, bootstyle="secondary")
                file_frame.pack(fill=X, pady=(5, 0))
                
                ttk.Label(
                    file_frame,
                    text=f"📎 {file_name}",
                    font=("Arial", 10),
                    bootstyle="inverse-secondary"
                ).pack(side=LEFT)
                
                def download_file(path=file_path, name=file_name):
                    from tkinter import filedialog
                    import shutil
                    
                    # Ask where to save
                    save_path = filedialog.asksaveasfilename(
                        title="Save submission file",
                        initialfile=name,
                        defaultextension=os.path.splitext(name)[1]
                    )
                    
                    if save_path:
                        try:
                            shutil.copy2(path, save_path)
                            messagebox.showinfo("Success", f"File downloaded to:\n{save_path}")
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not download file: {str(e)}")
                
                ttk.Button(
                    file_frame,
                    text="💾 Download",
                    command=download_file,
                    bootstyle="success-outline",
                    width=12
                ).pack(side=RIGHT, padx=(10, 0))
                
                # Open button
                def open_file(path=file_path):
                    import subprocess
                    if os.path.exists(path):
                        try:
                            subprocess.run(['open', path], check=True)
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not open file: {str(e)}")
                    else:
                        messagebox.showerror("Error", "File not found")
                
                ttk.Button(
                    file_frame,
                    text="👁️ Open",
                    command=open_file,
                    bootstyle="info-outline",
                    width=12
                ).pack(side=RIGHT, padx=(10, 0))
    
    def _on_closing(self):
        """Handle closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.client.disconnect()
            self.window.destroy()
