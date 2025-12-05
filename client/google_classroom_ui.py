#!/usr/bin/env python3
"""
LearnLive - Google Classroom Style UI
Modern desktop application using ttkbootstrap
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Canvas
from datetime import datetime


class LearnLiveApp:
    """Main application class for LearnLive"""
    
    def __init__(self):
        self.window = ttk.Window(themename="darkly")
        self.window.title("LearnLive - Google Classroom Style")
        self.window.geometry("1400x900")
        
        # Sample data
        self.classes = [
            {"id": 1, "name": "Computer Networks", "instructor": "Dr. Smith", "color": "#1967D2", "students": 45},
            {"id": 2, "name": "Data Structures", "instructor": "Prof. Johnson", "color": "#0D652D", "students": 38},
            {"id": 3, "name": "Machine Learning", "instructor": "Dr. Williams", "color": "#B80672", "students": 52},
            {"id": 4, "name": "Web Development", "instructor": "Prof. Brown", "color": "#E37400", "students": 41},
            {"id": 5, "name": "Database Systems", "instructor": "Dr. Garcia", "color": "#174EA6", "students": 36},
            {"id": 6, "name": "Operating Systems", "instructor": "Prof. Martinez", "color": "#9334E6", "students": 43},
        ]
        
        self.announcements = [
            {
                "instructor": "Dr. Smith",
                "time": "2 hours ago",
                "text": "Tomorrow's lecture will be held online via Zoom. Link will be shared 10 minutes before class.",
                "has_attachment": True
            },
            {
                "instructor": "Dr. Smith",
                "time": "Yesterday",
                "text": "Assignment 3 has been posted. Due date is next Friday at 11:59 PM.",
                "has_attachment": False
            },
            {
                "instructor": "Dr. Smith",
                "time": "3 days ago",
                "text": "Great job everyone on the midterm exam! Average score was 85%. Keep up the good work!",
                "has_attachment": False
            },
        ]
        
        self.current_class = None
        self.current_view = "home"
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=BOTH, expand=YES)
        
        # Sidebar
        self.sidebar = SidebarFrame(main_container, self.classes, self._on_class_select, self._on_home_click)
        self.sidebar.pack(side=LEFT, fill=Y)
        
        # Right container (header + content)
        right_container = ttk.Frame(main_container)
        right_container.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # Header
        self.header = HeaderFrame(right_container)
        self.header.pack(side=TOP, fill=X)
        
        # Content area
        self.content_frame = ttk.Frame(right_container)
        self.content_frame.pack(side=TOP, fill=BOTH, expand=YES)
        
        # Show home page by default
        self._show_home_page()
        
    def _show_home_page(self):
        """Display the home page with class cards"""
        self.current_view = "home"
        self.current_class = None
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create home page
        home = HomePage(self.content_frame, self.classes, self._on_class_card_click)
        home.pack(fill=BOTH, expand=YES)
        
        # Update sidebar highlight
        self.sidebar.highlight_home()
        
    def _show_class_page(self, class_data):
        """Display the class page"""
        self.current_view = "class"
        self.current_class = class_data
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create class page
        class_page = ClassPage(self.content_frame, class_data, self.announcements)
        class_page.pack(fill=BOTH, expand=YES)
        
    def _on_home_click(self):
        """Handle home button click"""
        self._show_home_page()
        
    def _on_class_select(self, class_id):
        """Handle class selection from sidebar"""
        class_data = next((c for c in self.classes if c["id"] == class_id), None)
        if class_data:
            self._show_class_page(class_data)
            
    def _on_class_card_click(self, class_id):
        """Handle class card click from home page"""
        class_data = next((c for c in self.classes if c["id"] == class_id), None)
        if class_data:
            self._show_class_page(class_data)
            self.sidebar.highlight_class(class_id)
    
    def run(self):
        """Start the application"""
        self.window.mainloop()


class SidebarFrame(ttk.Frame):
    """Left sidebar with navigation"""
    
    def __init__(self, parent, classes, on_class_select, on_home_click):
        super().__init__(parent, style="dark", width=280)
        self.classes = classes
        self.on_class_select = on_class_select
        self.on_home_click = on_home_click
        self.class_buttons = {}
        self.home_btn = None
        
        self.pack_propagate(False)
        
        self._build_sidebar()
        
    def _build_sidebar(self):
        """Build sidebar components"""
        # Logo section
        logo_frame = ttk.Frame(self, style="dark")
        logo_frame.pack(fill=X, pady=20, padx=20)
        
        logo_label = ttk.Label(
            logo_frame,
            text="🎓 LearnLive",
            font=("Arial", 20, "bold"),
            bootstyle="inverse-light"
        )
        logo_label.pack(anchor=W)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self, style="dark")
        nav_frame.pack(fill=X, padx=10, pady=10)
        
        self.home_btn = ttk.Button(
            nav_frame,
            text="🏠  Home",
            command=self.on_home_click,
            bootstyle="dark",
            width=25
        )
        self.home_btn.pack(fill=X, pady=2)
        
        ttk.Button(
            nav_frame,
            text="📅  Calendar",
            bootstyle="dark",
            width=25
        ).pack(fill=X, pady=2)
        
        ttk.Button(
            nav_frame,
            text="📚  Enrolled",
            bootstyle="dark",
            width=25
        ).pack(fill=X, pady=2)
        
        ttk.Button(
            nav_frame,
            text="✓  To-Do",
            bootstyle="dark",
            width=25
        ).pack(fill=X, pady=2)
        
        # Separator
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Classes section
        classes_label = ttk.Label(
            self,
            text="Enrolled Classes",
            font=("Arial", 11, "bold"),
            bootstyle="inverse-secondary"
        )
        classes_label.pack(anchor=W, padx=20, pady=(10, 5))
        
        # Scrollable classes list
        classes_container = ttk.Frame(self, style="dark")
        classes_container.pack(fill=BOTH, expand=YES, padx=10)
        
        canvas = Canvas(classes_container, bg="#222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(classes_container, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add class buttons
        for cls in self.classes:
            btn = ttk.Button(
                scrollable_frame,
                text=f"📖  {cls['name']}",
                command=lambda c=cls['id']: self._on_class_click(c),
                bootstyle="dark",
                width=25
            )
            btn.pack(fill=X, pady=2, padx=5)
            self.class_buttons[cls['id']] = btn
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def _on_class_click(self, class_id):
        """Handle class button click"""
        self.on_class_select(class_id)
        self.highlight_class(class_id)
        
    def highlight_home(self):
        """Highlight home button"""
        if self.home_btn:
            self.home_btn.configure(bootstyle="primary")
        for btn in self.class_buttons.values():
            btn.configure(bootstyle="dark")
            
    def highlight_class(self, class_id):
        """Highlight selected class"""
        if self.home_btn:
            self.home_btn.configure(bootstyle="dark")
        for cid, btn in self.class_buttons.items():
            if cid == class_id:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="dark")


class HeaderFrame(ttk.Frame):
    """Top header bar"""
    
    def __init__(self, parent):
        super().__init__(parent, bootstyle="dark")
        self._build_header()
        
    def _build_header(self):
        """Build header components"""
        # Search bar
        search_frame = ttk.Frame(self, bootstyle="dark")
        search_frame.pack(side=LEFT, fill=X, expand=YES, padx=20, pady=15)
        
        search_entry = ttk.Entry(
            search_frame,
            font=("Arial", 12),
            width=50
        )
        search_entry.insert(0, "🔍 Search classes...")
        search_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # User section
        user_frame = ttk.Frame(self, bootstyle="dark")
        user_frame.pack(side=RIGHT, padx=20)
        
        ttk.Button(
            user_frame,
            text="➕",
            bootstyle="primary-outline",
            width=3
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            user_frame,
            text="👤",
            bootstyle="primary-outline",
            width=3
        ).pack(side=LEFT, padx=5)


class HomePage(ttk.Frame):
    """Home page with class cards grid"""
    
    def __init__(self, parent, classes, on_card_click):
        super().__init__(parent, bootstyle="dark")
        self.classes = classes
        self.on_card_click = on_card_click
        
        self._build_home()
        
    def _build_home(self):
        """Build home page"""
        # Title
        title_frame = ttk.Frame(self, bootstyle="dark")
        title_frame.pack(fill=X, padx=30, pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="Your Classes",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        )
        title_label.pack(anchor=W)
        
        # Scrollable canvas for cards
        canvas = Canvas(self, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
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
        
        row = 0
        col = 0
        for cls in self.classes:
            card = self._create_class_card(cards_container, cls)
            card.grid(row=row, column=col, padx=15, pady=15, sticky=NSEW)
            
            col += 1
            if col >= 3:  # 3 cards per row
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            cards_container.columnconfigure(i, weight=1)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def _create_class_card(self, parent, class_data):
        """Create a single class card"""
        # Card frame
        card = ttk.Frame(parent, bootstyle="secondary", relief=RAISED)
        card.configure(width=350, height=280)
        card.pack_propagate(False)
        
        # Color bar at top (using label with colored background)
        color_label = ttk.Label(
            card,
            text="",
            background=class_data["color"]
        )
        color_label.pack(fill=X, ipady=50)
        
        # Class name overlay on color bar
        name_frame = ttk.Frame(card)
        name_frame.place(relx=0.05, rely=0.15, anchor=W)
        
        name_label = ttk.Label(
            name_frame,
            text=class_data["name"],
            font=("Arial", 18, "bold"),
            foreground="white",
            background=class_data["color"]
        )
        name_label.pack(anchor=W)
        
        # Content section
        content_frame = ttk.Frame(card, bootstyle="secondary")
        content_frame.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        # Instructor
        instructor_label = ttk.Label(
            content_frame,
            text=class_data["instructor"],
            font=("Arial", 12),
            bootstyle="inverse-secondary"
        )
        instructor_label.pack(anchor=W, pady=(0, 5))
        
        # Students count
        students_label = ttk.Label(
            content_frame,
            text=f"{class_data['students']} students",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        )
        students_label.pack(anchor=W)
        
        # Spacer
        ttk.Frame(content_frame).pack(fill=BOTH, expand=YES)
        
        # Bottom icons
        icons_frame = ttk.Frame(content_frame, bootstyle="secondary")
        icons_frame.pack(side=BOTTOM, fill=X)
        
        ttk.Label(icons_frame, text="📝", font=("Arial", 16)).pack(side=LEFT, padx=5)
        ttk.Label(icons_frame, text="📁", font=("Arial", 16)).pack(side=LEFT, padx=5)
        ttk.Label(icons_frame, text="⋮", font=("Arial", 16)).pack(side=RIGHT, padx=5)
        
        # Make card clickable
        def on_click(e):
            self.on_card_click(class_data["id"])
        
        card.bind("<Button-1>", on_click)
        color_label.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        
        return card


class ClassPage(ttk.Frame):
    """Class page with tabs"""
    
    def __init__(self, parent, class_data, announcements):
        super().__init__(parent, bootstyle="dark")
        self.class_data = class_data
        self.announcements = announcements
        
        self._build_class_page()
        
    def _build_class_page(self):
        """Build class page"""
        # Banner
        banner = ttk.Frame(self, height=150)
        banner.pack(fill=X)
        banner.pack_propagate(False)
        
        # Banner with color
        banner_label = ttk.Label(
            banner,
            text="",
            background=self.class_data["color"]
        )
        banner_label.pack(fill=BOTH, expand=YES)
        
        # Class title on banner
        title_frame = ttk.Frame(banner)
        title_frame.place(relx=0.05, rely=0.5, anchor=W)
        
        class_title = ttk.Label(
            title_frame,
            text=self.class_data["name"],
            font=("Arial", 28, "bold"),
            foreground="white",
            background=self.class_data["color"]
        )
        class_title.pack(anchor=W)
        
        instructor_label = ttk.Label(
            title_frame,
            text=self.class_data["instructor"],
            font=("Arial", 14),
            foreground="white",
            background=self.class_data["color"]
        )
        instructor_label.pack(anchor=W, pady=(5, 0))
        
        # Tabbed interface
        notebook = ttk.Notebook(self, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Stream tab
        stream_tab = StreamTab(notebook, self.announcements)
        notebook.add(stream_tab, text="Stream")
        
        # Classwork tab
        classwork_tab = ClassworkTab(notebook)
        notebook.add(classwork_tab, text="Classwork")
        
        # People tab
        people_tab = PeopleTab(notebook, self.class_data)
        notebook.add(people_tab, text="People")


class StreamTab(ttk.Frame):
    """Stream tab with announcements"""
    
    def __init__(self, parent, announcements):
        super().__init__(parent, bootstyle="dark")
        self.announcements = announcements
        
        self._build_stream()
        
    def _build_stream(self):
        """Build stream tab"""
        # New announcement button
        btn_frame = ttk.Frame(self, bootstyle="dark")
        btn_frame.pack(fill=X, padx=20, pady=15)
        
        ttk.Button(
            btn_frame,
            text="➕ New Announcement",
            bootstyle="primary",
            width=25
        ).pack(side=LEFT)
        
        # Announcements feed
        feed_canvas = Canvas(self, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=feed_canvas.yview)
        scrollable_frame = ttk.Frame(feed_canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: feed_canvas.configure(scrollregion=feed_canvas.bbox("all"))
        )
        
        feed_canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        feed_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add announcements
        for announcement in self.announcements:
            self._create_announcement_tile(scrollable_frame, announcement)
        
        feed_canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def _create_announcement_tile(self, parent, announcement):
        """Create an announcement tile"""
        tile = ttk.Frame(parent, bootstyle="secondary", relief=RAISED)
        tile.pack(fill=X, padx=20, pady=10)
        
        content = ttk.Frame(tile, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=20, pady=15)
        
        # Header
        header = ttk.Frame(content, bootstyle="secondary")
        header.pack(fill=X, pady=(0, 10))
        
        # Avatar circle
        avatar = ttk.Label(
            header,
            text="👤",
            font=("Arial", 20),
            bootstyle="inverse-secondary"
        )
        avatar.pack(side=LEFT, padx=(0, 10))
        
        # Instructor and time
        info_frame = ttk.Frame(header, bootstyle="secondary")
        info_frame.pack(side=LEFT, fill=X, expand=YES)
        
        instructor_label = ttk.Label(
            info_frame,
            text=announcement["instructor"],
            font=("Arial", 12, "bold"),
            bootstyle="inverse-secondary"
        )
        instructor_label.pack(anchor=W)
        
        time_label = ttk.Label(
            info_frame,
            text=announcement["time"],
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        )
        time_label.pack(anchor=W)
        
        # Message
        message_label = ttk.Label(
            content,
            text=announcement["text"],
            font=("Arial", 11),
            bootstyle="inverse-secondary",
            wraplength=900,
            justify=LEFT
        )
        message_label.pack(anchor=W, pady=(0, 10))
        
        # Attachment icon
        if announcement["has_attachment"]:
            attachment_frame = ttk.Frame(content, bootstyle="info", relief=SOLID)
            attachment_frame.pack(fill=X, pady=(10, 0))
            
            ttk.Label(
                attachment_frame,
                text="📎 Attachment.pdf",
                font=("Arial", 10),
                bootstyle="inverse-info"
            ).pack(anchor=W, padx=10, pady=5)


class ClassworkTab(ttk.Frame):
    """Classwork tab with assignments"""
    
    def __init__(self, parent):
        super().__init__(parent, bootstyle="dark")
        
        self._build_classwork()
        
    def _build_classwork(self):
        """Build classwork tab"""
        # Create assignment button
        btn_frame = ttk.Frame(self, bootstyle="dark")
        btn_frame.pack(fill=X, padx=20, pady=15)
        
        ttk.Button(
            btn_frame,
            text="➕ Create Assignment",
            bootstyle="primary",
            width=25
        ).pack(side=LEFT)
        
        # Scrollable assignments list
        canvas = Canvas(self, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Sample assignments
        assignments = [
            {"title": "Assignment 1: Network Protocols", "due": "Due Dec 10", "points": "100 pts"},
            {"title": "Quiz 2: TCP/IP", "due": "Due Dec 5", "points": "50 pts"},
            {"title": "Project: Build a Chat App", "due": "Due Dec 20", "points": "200 pts"},
            {"title": "Reading: Chapter 5", "due": "Due Dec 3", "points": "No points"},
        ]
        
        for assignment in assignments:
            self._create_assignment_tile(scrollable_frame, assignment)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def _create_assignment_tile(self, parent, assignment):
        """Create an assignment tile"""
        tile = ttk.Frame(parent, bootstyle="secondary", relief=RAISED)
        tile.pack(fill=X, padx=20, pady=10)
        
        content = ttk.Frame(tile, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=20, pady=15)
        
        # Icon and title
        header = ttk.Frame(content, bootstyle="secondary")
        header.pack(fill=X)
        
        ttk.Label(
            header,
            text="📝",
            font=("Arial", 20),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=(0, 10))
        
        title_label = ttk.Label(
            header,
            text=assignment["title"],
            font=("Arial", 12, "bold"),
            bootstyle="inverse-secondary"
        )
        title_label.pack(side=LEFT, fill=X, expand=YES)
        
        # Due date and points
        info_frame = ttk.Frame(content, bootstyle="secondary")
        info_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Label(
            info_frame,
            text=assignment["due"],
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=(35, 20))
        
        ttk.Label(
            info_frame,
            text=assignment["points"],
            font=("Arial", 10),
            bootstyle="inverse-info"
        ).pack(side=LEFT)


class PeopleTab(ttk.Frame):
    """People tab with instructors and students"""
    
    def __init__(self, parent, class_data):
        super().__init__(parent, bootstyle="dark")
        self.class_data = class_data
        
        self._build_people()
        
    def _build_people(self):
        """Build people tab"""
        canvas = Canvas(self, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Instructors section
        instructor_section = ttk.Frame(scrollable_frame, bootstyle="dark")
        instructor_section.pack(fill=X, padx=20, pady=20)
        
        ttk.Label(
            instructor_section,
            text="Instructors",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, pady=(0, 10))
        
        self._create_person_tile(instructor_section, self.class_data["instructor"], "Instructor")
        
        # Students section
        students_section = ttk.Frame(scrollable_frame, bootstyle="dark")
        students_section.pack(fill=X, padx=20, pady=20)
        
        ttk.Label(
            students_section,
            text=f"Students ({self.class_data['students']})",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, pady=(0, 10))
        
        # Sample students
        sample_students = [
            "Alice Johnson", "Bob Smith", "Charlie Brown", "David Wilson",
            "Emma Davis", "Frank Miller", "Grace Lee", "Henry Taylor"
        ]
        
        for student in sample_students:
            self._create_person_tile(students_section, student, "Student")
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def _create_person_tile(self, parent, name, role):
        """Create a person tile"""
        tile = ttk.Frame(parent, bootstyle="secondary", relief=RAISED)
        tile.pack(fill=X, pady=5)
        
        content = ttk.Frame(tile, bootstyle="secondary")
        content.pack(fill=X, padx=15, pady=10)
        
        # Avatar
        ttk.Label(
            content,
            text="👤",
            font=("Arial", 18),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=(0, 15))
        
        # Name and role
        info_frame = ttk.Frame(content, bootstyle="secondary")
        info_frame.pack(side=LEFT, fill=X, expand=YES)
        
        ttk.Label(
            info_frame,
            text=name,
            font=("Arial", 11, "bold"),
            bootstyle="inverse-secondary"
        ).pack(anchor=W)
        
        ttk.Label(
            info_frame,
            text=role,
            font=("Arial", 9),
            bootstyle="inverse-secondary"
        ).pack(anchor=W)


if __name__ == "__main__":
    app = LearnLiveApp()
    app.run()
