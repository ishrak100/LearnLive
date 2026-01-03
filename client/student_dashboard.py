import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Canvas, simpledialog
import os
import sys
import threading
import queue

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.utility import LearnLiveClient
from client.expand_gui import ExpandView
from client.discussion_gui import DiscussionView


class StudentDashboard:
    """Student Dashboard - Google Classroom Style"""
    
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
        self.notification_history = []  # Store notification history
        self.search_query = ""
        self.announcements = []
        self.announcements_cache = {}  # Cache announcements by class_id to reduce queries
        self.last_refresh_time = {}  # Track last refresh time per class
        self.pending_refresh = {}  # Debounce refresh requests per class
        self.materials = []  # Track class materials
        self.materials_container = None  # Reference to materials display container
        self.assignments = []  # Track class assignments
        self.assignments_container = None  # Reference to assignments display container
        self.pending_submission_request = None  # Track pending submission requests
        self.current_expand_view = None  # Track current expanded view for comments
        
        self.client.set_message_callback(self._handle_server_message)
    
    def show(self):
        """Show dashboard"""
        self.window = ttk.Window(themename="minty")
        self.window.title(f"LearnLive - {self.user_data.get('name', 'Student')}")
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
        
        ttk.Button(
            nav_frame, 
            text="✓  To-Do", 
            command=self._show_todo_page,
            bootstyle="dark", 
            width=25
        ).pack(fill=X, pady=2)
        
        ttk.Button(
            nav_frame, 
            text="🔔  Notifications", 
            command=self._show_email_notification_page,
            bootstyle="dark", 
            width=25
        ).pack(fill=X, pady=2)
        
        ttk.Separator(sidebar, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Classes
        ttk.Label(
            sidebar,
            text="Enrolled Classes",
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
            ).pack(pady=20)
            return
        
        canvas = Canvas(self.classes_frame, bg="#222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.classes_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="dark")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        filtered_classes = self._filter_classes()
        for cls in filtered_classes:
            ttk.Button(
                scrollable_frame,
                text=f"📖  {cls.get('class_name', 'Unknown')}",
                command=lambda c=cls: self._show_class_page(c),
                bootstyle="dark",
                width=45
            ).pack(fill=X, pady=2, padx=5)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _create_header(self, parent):
        """Create header"""
        header = ttk.Frame(parent, bootstyle="dark")
        
        # Search
        search_frame = ttk.Frame(header, bootstyle="dark")
        search_frame.pack(side=LEFT, fill=X, expand=YES, padx=20, pady=15)
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 12), width=50)
        self.search_entry.insert(0, "🔍 Search classes...")
        self.search_entry.pack(side=LEFT, fill=X, expand=YES)
        
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        
        # User
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
        """Show home page"""
        self.current_view = "home"
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.content_frame.configure(bootstyle="dark", borderwidth=1)
        if self.home_btn:
            self.home_btn.configure(bootstyle="dark")
        
        # Title
        title_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        title_frame.pack(fill=X, padx=30, pady=20)
        
        ttk.Label(
            title_frame,
            text="My Classroom",
            font=("Arial", 24, "bold"),
            bootstyle="dark"
        ).pack(anchor=W)
        
        if not self.classes:
            self._show_empty_state()
            return
        
        # Canvas for scrolling
        canvas = Canvas(self.content_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="light")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Cards grid
        cards_container = ttk.Frame(scrollable_frame, bootstyle="light")
        cards_container.pack(fill=BOTH, expand=YES, padx=30, pady=10)
        
        filtered_classes = self._filter_classes()
        row, col = 0, 0
        for cls in filtered_classes:
            card = self._create_class_card(cards_container, cls)
            card.grid(row=row, column=col, padx=15, pady=15, sticky=NSEW)
            col += 1
            if col >= 3:
                col, row = 0, row + 1
        
        for i in range(3):
            cards_container.columnconfigure(i, weight=1)   
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _show_empty_state(self):
        """Show empty state"""
        empty = ttk.Frame(self.content_frame, bootstyle="light")
        empty.pack(fill=BOTH, expand=YES)
        
        center = ttk.Frame(empty, bootstyle="light")
        center.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        ttk.Label(center, text="📚", font=("Arial", 80), bootstyle="inverse-secondary").pack(pady=20)
        ttk.Label(center, text="No classes yet", font=("Arial", 24, "bold"), bootstyle="inverse-light").pack(pady=10)
        ttk.Label(center, text="Join a class using the class code from your teacher", font=("Arial", 12), bootstyle="inverse-secondary").pack(pady=5)
        ttk.Button(center, text="+ Join Class", bootstyle="primary", command=self._join_class_dialog, width=20).pack(pady=20)
    
    def _create_class_card(self, parent, class_data):
        """Create class card"""

        color = "#000000"
        
        card = ttk.Frame(parent, bootstyle="dark")
        
        # Color banner (black box with class name and subject)
        banner = Canvas(card, height=80, bg="#000000", highlightthickness=100)
        banner.pack(fill=X)
        
        # Class name in banner
        banner.create_text(
            15, 15,
            text=class_data.get("class_name", "Unknown"),
            anchor=NW,
            fill="black",
            font=("Arial", 16, "bold")
        )
        
        # Subject in banner
        banner.create_text(
            15, 45,
            text=class_data.get("teacher_name", ""),
            anchor=NW,
            fill="black",
            font=("Arial", 11)
        )
        
        # Content area below the banner
        content = ttk.Frame(card, bootstyle="secondary")
        content.pack(fill=BOTH, expand=YES, padx=2, pady=2)

        # Subject name (first position)
        subject_name = class_data.get('subject', 'Subject')
        ttk.Label(
            content,
            text=f" 🎓Subject: {subject_name}",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=15, pady=(15, 5))
        
        # Section
        section = class_data.get('section', '')
        if section:
            ttk.Label(
                content,
                text=f"📋 Section: {section}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, padx=15, pady=(0, 5))
        
        # Room
        room = class_data.get('room', '')
        if room:
            ttk.Label(
                content,
                text=f"🚪 Room: {room}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, padx=15, pady=(0, 5))
        
        # Total Students
        total_students = len(class_data.get('students', []))
        ttk.Label(
            content,
            text=f"Students: {total_students}",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, padx=15, pady=(0, 15))
        
        # Click handlers
        card.bind("<Button-1>", lambda e: self._show_class_page(class_data))
        banner.bind("<Button-1>", lambda e: self._show_class_page(class_data))
        
        return card
    
    def _show_class_page(self, class_data):
      """Show class page"""
      self.current_view = "class"
      self.selected_class = class_data

  
      for widget in self.content_frame.winfo_children():
         widget.destroy()

      if self.home_btn:
        self.home_btn.configure(bootstyle="dark")

        import tkinter as tk

        banner = tk.Frame(
        self.content_frame,
        bg="#000000",
        height=150
       )
      banner.pack(fill=tk.X)
      banner.pack_propagate(False)

      title_frame = tk.Frame(banner, bg="#000000")
      title_frame.place(relx=0.05, rely=0.5, anchor="w")

      tk.Label(
       title_frame,
       text=class_data.get("class_name", "Unknown"),
       font=("Arial", 28, "bold"),
       fg="white",
       bg="#000000"
     ).pack(anchor="w")

      tk.Label(
      title_frame,
      text=class_data.get("subject", ""),
      font=("Arial", 14),
      fg="white",
      bg="#000000"
     ).pack(anchor="w", pady=(5, 0))


      notebook = ttk.Notebook(self.content_frame, bootstyle="dark")
      notebook.pack(fill=BOTH, expand=YES, padx=20, pady=20)

      stream = ttk.Frame(notebook, bootstyle="light")
      notebook.add(stream, text="Announcements")

      self.stream_canvas = Canvas(stream, bg="#FFFFFF", highlightthickness=0)
      scrollbar = ttk.Scrollbar(stream, orient="vertical", command=self.stream_canvas.yview)
      self.stream_container = ttk.Frame(self.stream_canvas, bootstyle="light")

      self.stream_container.bind(
         "<Configure>",
        lambda e: self.stream_canvas.configure(
             scrollregion=self.stream_canvas.bbox("all")
         )
      )

      self.stream_canvas_window = self.stream_canvas.create_window(
        (0, 0),
        window=self.stream_container,
        anchor="nw"
      )

      self.stream_canvas.configure(yscrollcommand=scrollbar.set)
      self.stream_canvas.bind(
        "<Configure>",
        lambda e: self.stream_canvas.itemconfig(
            self.stream_canvas_window, width=e.width
        )
      )

      self.stream_canvas.pack(side=LEFT, fill=BOTH, expand=YES, padx=20, pady=20)
      scrollbar.pack(side=RIGHT, fill=Y)

      if self.selected_class:
        self.client.view_announcements(self.selected_class["_id"])

      assignments = ttk.Frame(notebook, bootstyle="light")
      self._create_assignments_tab(assignments)
      notebook.add(assignments, text="Assignments")

   
      materials = ttk.Frame(notebook, bootstyle="light")
      self._create_materials_tab(materials)
      notebook.add(materials, text="Class Materials")
  
      people = ttk.Frame(notebook, bootstyle="light")
      self._create_people_tab(people, class_data)
      notebook.add(people, text="People")

      discussion = ttk.Frame(notebook, bootstyle="light")
      notebook.add(discussion, text="Discussion")

      discussion_view = DiscussionView(self)
      discussion_view.create_tab_content(discussion)




    
    def _create_assignments_tab(self, parent):
        """Create assignments tab"""
        ttk.Label(
            parent,
            text="Assignments",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=20)
        
        # Assignments container
        assignments_container = ttk.Frame(parent, bootstyle="light")
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
        
        # Materials container with scrollbar
        materials_container = ttk.Frame(parent, bootstyle="light")
        materials_container.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        
        # Store reference for updates
        self.materials_container = materials_container
        
        # Fetch and display materials
        if self.selected_class:
            self.client.view_materials(self.selected_class['_id'])
    
    def show_expanded_view(self, item_type, item_data):
        """Show expanded view for an item"""
        expand_view = ExpandView(self, item_type, item_data)
        self.current_expand_view = expand_view
        expand_view.show()
    
    def _update_stream_display(self):
        """Update the stream display with announcements"""
        print(f"[DEBUG STUDENT] _update_stream_display called, announcements count: {len(self.announcements)}")
        
        if not hasattr(self, 'stream_container'):
            print("[DEBUG STUDENT] No stream_container attribute")
            return
        
        try:
            # Check if the widget still exists
            self.stream_container.winfo_exists()
        except:
            return
        
        # Clear existing widgets
        for widget in self.stream_container.winfo_children():
            widget.destroy()
        
        if not self.announcements:
            ttk.Label(
                self.stream_container,
                text="No announcements yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            return
        
        # Display announcements
        for announcement in self.announcements:
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
            
            # Expand button
            ttk.Button(
                frame,
                text="🔍 Expand",
                command=lambda ann=announcement: self.show_expanded_view('announcement', {**ann, 'class_id': self.selected_class['_id']}),
                bootstyle="outline-secondary"
            ).pack(anchor=E, pady=(5, 0))
        
        # Update canvas scroll region after adding content
        if hasattr(self, 'stream_canvas'):
            try:
                self.stream_container.update_idletasks()
                self.stream_canvas.configure(scrollregion=self.stream_canvas.bbox("all"))
            except:
                pass
    
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
                text="No assignments yet",
                font=("Arial", 11),
                bootstyle="inverse-secondary"
            ).pack(padx=20, pady=20)
            return

        # Create scrollable frame
        from tkinter import Canvas, Scrollbar
        canvas = Canvas(self.assignments_container, bg="#FFFFFF", highlightthickness=0)
        scrollbar = Scrollbar(self.assignments_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="light")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        # ADD THIS BINDING TO MAKE FRAME FULL WIDTH
        canvas.bind(
             "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
        )

         # Pack canvas and scrollbar to occupy the full available space
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Display each assignment - CHANGED FROM grid() TO pack()
        for assignment in self.assignments:
            assignment_frame = ttk.Frame(scrollable_frame, bootstyle="light")
            # Changed from grid() to pack() with fill=X
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

            max_points = assignment.get('max_points', 100)
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

            # Submit button
            ttk.Button(
                info_frame,
                text="📤 Submit Assignment",
                bootstyle="success-outline",
                command=lambda assignment=assignment: self.submit_assignment(assignment),
                width=15
            ).pack(anchor=E, pady=(5, 0))

            # Expand button
            ttk.Button(
                info_frame,
                text="🔍 Expand",
                command=lambda assignment=assignment: self.show_expanded_view('assignment', {**assignment, 'class_id': self.selected_class['_id']}),
                bootstyle="outline-secondary"
            ).pack(anchor=E, pady=(5, 0))


        # Expand button added to the materials section
    def submit_assignment(self, assignment):
            """Handle assignment submission by the student"""
            from tkinter import filedialog, messagebox, simpledialog
            import os

            # Ensure the assignment object contains '_id'
            if '_id' not in assignment:
                messagebox.showerror("Error", "Assignment ID is missing")
                return

            # Get user ID safely with fallbacks
            user_id = None
            if hasattr(self, 'user_data') and self.user_data:
                user_id = (
                    self.user_data.get('_id') or 
                    self.user_data.get('id') or 
                    self.user_data.get('user_id') or 
                    self.user_data.get('userId')
                )
    
             # If still no user_id, show error
            if not user_id:
                messagebox.showerror("Error", "User ID not found. Please login again.")
                return

             # Ask for optional text comment
            text_content = simpledialog.askstring(
                "Assignment Comment",
                "Enter optional comments about your submission (or leave empty):",
                parent=self.window
            )

            if text_content is None:  # User cancelled
                return

        # Ask for file
            file_path = filedialog.askopenfilename(
                title="Select file to submit",
                filetypes=[("All Files", "*.*"), ("PDF Files", "*.pdf"), 
                          ("Word Documents", "*.docx"), ("Text Files", "*.txt")]
            )

            if not file_path:  # User cancelled file selection
                return

            try:
                with open(file_path, 'rb') as file:
                    file_content = file.read()  # Read the file content as binary

                filename = os.path.basename(file_path)

                print(f"[CLIENT DEBUG] Submitting assignment:")
                print(f"  Assignment ID: {assignment['_id']}")
                print(f"  User ID: {user_id}")
                print(f"  Filename: {filename}")
                print(f"  File size: {len(file_content)} bytes")
                print(f"  Text content: '{text_content}'")

                 # Call the updated submit_assignment method with binary data
                self.client.submit_assignment_gridfs(
                    assignment_id=assignment['_id'],
                    user_id=user_id,
                    file_content=file_content,
                    submission_text=text_content,
                    filename=filename
                )
        
                messagebox.showinfo("Success", "Assignment submitted! Processing with GridFS...")
        
            except Exception as e:
                print(f"[CLIENT ERROR] Exception: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"An error occurred: {str(e)}")



    
    def _display_materials(self):
        """Display materials in classwork tab - GridFS ONLY"""
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

    # Create window FIRST
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
        # NOW define the function that uses window_id
        def configure_scrollable(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Force the scrollable frame to match canvas width
            canvas.itemconfig(window_id, width=e.width)

        scrollable_frame.bind("<Configure>", configure_scrollable)
    
        canvas.configure(yscrollcommand=scrollbar.set)
    
    # You can keep this binding too, or remove it since configure_scrollable already does it
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
        )

        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Display each material
        for idx, material in enumerate(self.materials):
            # Skip materials without file_id (invalid)
            file_id = material.get('file_id') or material.get('file_id_str')
            if not file_id:
                continue
    
            material_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
            material_frame.pack(fill=X, padx=10, pady=5)

            # Material card
            card = ttk.Frame(material_frame, bootstyle="secondary", relief="raised")
            card.pack(fill=X, padx=5, pady=5, expand=True)   
            # Material info
            info_frame = ttk.Frame(card, bootstyle="secondary")
            info_frame.pack(fill=X, padx=15, pady=10, expand=True)

            # Title and type
            title_text = material.get('title', 'Untitled')
            mat_type = material.get('material_type', 'Document')
            filename = material.get('filename', 'Material file')
            uploaded_at = material.get('uploaded_at', '')
            teacher_name = material.get('teacher_name', '')

            # Header with title
            header_frame = ttk.Frame(info_frame, bootstyle="secondary")
            header_frame.pack(fill=X, anchor=W)

            ttk.Label(
                header_frame,
                text=f"📎 {title_text}",
                font=("Arial", 12, "bold"),
                bootstyle="inverse-secondary"
            ).pack(side=LEFT)

            
            def create_download_handler(fid, fname):
                def handler():
                    """Download material"""
                    print(f"[DEBUG STUDENT] Downloading material: {fname}, file_id: {fid}")
        
                    # Send download request
                    result = self.client.download_file_binary(fid)
        
                    if not result.get('success'):
                        from tkinter import messagebox
                        messagebox.showerror("Error", f"Failed to start download: {result.get('error')}")
                    else:
                       print(f"[DEBUG STUDENT] Download request sent: {result.get('request_id')}")
                    # DEFAULT IS SAVE MODE - no want_to_open attribute
                    # This will trigger _save_downloaded_file in the handler
                return handler

            # Create download handler for this material
            download_handler = create_download_handler(file_id, filename)

            # Download button - SAME as before but now it works
            ttk.Button(
                header_frame,
                text="⬇️ Download",
                bootstyle="info-outline",
                command=download_handler,
                width=12
            ).pack(side=RIGHT, padx=(10, 0))
 
            # Material type
            ttk.Label(
                info_frame,
                text=f"Type: {mat_type}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, pady=(5, 0))

            # File info
            ttk.Label(
                info_frame,
                text=f"File: {filename}",
                font=("Arial", 10),
                bootstyle="inverse-secondary"
            ).pack(anchor=W, pady=(2, 0))

            # Upload date
            if uploaded_at:
                ttk.Label(
                    info_frame,
                    text=f"Uploaded: {uploaded_at}",
                    font=("Arial", 9),
                    bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(2, 0))

            # Teacher name (if available)
            if teacher_name:
                ttk.Label(
                    info_frame,
                    text=f"By: {teacher_name}",
                    font=("Arial", 9, "italic"),
                     bootstyle="inverse-secondary"
                ).pack(anchor=W, pady=(2, 0))

        # Create expand handler with captured material
            def create_expand_handler(mat):
                def handler():
                    self.show_expanded_view('material', {
                        **mat, 
                        'class_id': self.selected_class['_id']
                    })
                return handler

            expand_handler = create_expand_handler(material)

            # Expand button
            ttk.Button(
                info_frame,
                text="🔍 Expand",
                command=expand_handler,
                bootstyle="outline-secondary"
            ).pack(pady=(5, 0))
    
    def _create_people_tab(self, parent, class_data):
        """Create people tab with teacher and students"""
        # Teacher section
        ttk.Label(
            parent,
            text="Teacher",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, padx=20, pady=(20, 10))
        
        teacher_frame = ttk.Frame(parent, bootstyle="secondary")
        teacher_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        teacher_name = class_data.get('teacher_name', 'Teacher')
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
        
        student_list = class_data.get('student_list', [])
        
        if student_list:
            # Create scrollable frame for students
            canvas = Canvas(parent, bg="#222", highlightthickness=0, height=300)
            scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
            students_container = ttk.Frame(canvas, bootstyle="dark")
            
            students_container.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            window_id = canvas.create_window((0, 0), window=students_container, anchor="nw")

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
            )

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
    
    def _join_class_dialog(self):
        """Join class dialog"""
        # Create custom dialog with dark theme
        from tkinter import Toplevel
        dialog = Toplevel(self.window)
        dialog.title("Join Class")
        dialog.geometry("450x250")
        dialog.configure(bg='#222222')
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=30, bootstyle="dark")
        frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(
            frame,
            text="Join Class",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(pady=(0, 20))
        
        ttk.Label(
            frame,
            text="Enter Class Code:",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        code_entry = ttk.Entry(frame, font=("Arial", 13))
        code_entry.pack(fill=X, pady=(0, 20))
        code_entry.focus()
        
        def join():
            class_code = code_entry.get().strip()
            if class_code:
                self.client.join_class(class_code)
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter a class code")
        
        # Buttons
        btn_frame = ttk.Frame(frame, bootstyle="dark")
        btn_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        ).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="Join",
            bootstyle="primary",
            command=join,
            width=15
        ).pack(side=RIGHT)
        
        # Bind Enter key
        code_entry.bind("<Return>", lambda e: join())
    
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
        
        self._update_sidebar_classes()
        if self.current_view == "home":
            self._show_home_page()
    
    def _filter_classes(self):
        """Filter classes based on search query"""
        if not self.search_query:
            return self.classes
        
        filtered = []
        for cls in self.classes:
            if (self.search_query in cls.get('class_name', '').lower() or
                self.search_query in cls.get('subject', '').lower() or
                self.search_query in cls.get('section', '').lower() or
                self.search_query in cls.get('room', '').lower()):
                filtered.append(cls)
        
        return filtered
    
    def _handle_server_message(self, message: dict):
        """Handle server messages"""
        msg_type = message.get("type", "")
        print(f"[DEBUG STUDENT] _handle_server_message: type={msg_type}, keys={message.keys()}")
        if msg_type == 'FILE_DOWNLOAD_COMPLETE':
            print(f"[DEBUG STUDENT] File download complete: {message.get('filename')}")
    
            binary_data = message.get('binary_data')
            filename = message.get('filename')
            request_id = message.get('request_id')
    
            print(f"[DEBUG STUDENT] Request ID: {request_id}, Binary data size: {len(binary_data) if binary_data else 0}")
    
            if binary_data and filename:
                # CRITICAL FIX: Use window.after() to prevent UI blocking
                if hasattr(self, f'want_to_open_{request_id}'):
                    # Open the file
                    print(f"[DEBUG STUDENT] Opening file: {filename}")
                    delattr(self, f'want_to_open_{request_id}')
                    # Use after() to schedule in main thread
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: self._open_downloaded_file(filename, binary_data, request_id))
                else:
                    # Save the file - DEFAULT BEHAVIOR
                    print(f"[DEBUG STUDENT] Saving file: {filename}")
                    # Use after() to schedule in main thread
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: self._save_downloaded_file(filename, binary_data, request_id))
    
            # Clear binary data from message to save memory
            if 'binary_data' in message:
                message['binary_data'] = b''
    
            return

        
        if msg_type == "SUCCESS":
            if "classes" in message:
                self.classes = message.get("classes", [])
                self._update_sidebar_classes()
                if self.current_view == "home":
                    self._show_home_page()
            
            elif "submission_id" in message:
                # Handle SUBMIT_ASSIGNMENT success response
                print("[DEBUG STUDENT] Assignment submitted successfully, refreshing assignments")
                # Refresh assignments after a brief delay to ensure DB is updated
                if self.selected_class:
                    self.window.after(500, lambda: self.client.view_assignments(self.selected_class['_id']))
            elif "class_id" in message and message.get("success"):
                # Handle JOIN_CLASS success response - refresh class list
                print("[DEBUG STUDENT] Class joined successfully, refreshing class list")
                self.client.view_classes()
                messagebox.showinfo("Success", "You have successfully joined the class!")
            elif "announcements" in message:
                # Handle VIEW_ANNOUNCEMENTS response
                print(f"[DEBUG STUDENT] Received announcements: count={len(message.get('announcements', []))}")
                self.announcements = message.get("announcements", [])
                print(f"[DEBUG STUDENT] self.announcements set to: {len(self.announcements)} items")
                
                # Cache announcements for this class
                if self.selected_class:
                    class_id = self.selected_class["_id"]
                    self.announcements_cache[class_id] = self.announcements
                    print(f"[DEBUG STUDENT] Cached announcements for class: {class_id}")
                
                print(f"[DEBUG STUDENT] About to call _update_stream_display")
                if hasattr(self, 'window') and self.window:
                    self.window.after(0, self._update_stream_display)
                else:
                    self._update_stream_display()
                print(f"[DEBUG STUDENT] _update_stream_display scheduled")
            elif "notifications" in message:
                # Handle GET_NOTIFICATIONS response
                notifications = message.get("notifications", [])
                # Convert database notifications to display format
                self.notification_history = []
                unread_count = 0
                latest_unread = None
                
                for notif in notifications:
                    # Extract data from stored notification
                    notif_data = notif.get('data', {})
                    notif_data['received_at'] = notif.get('created_at', '')
                    self.notification_history.append(notif_data)
                    
                    # Count unread notifications
                    if not notif.get('read', False):
                        unread_count += 1
                        if latest_unread is None:
                            latest_unread = notif_data
                
                print(f"[DEBUG] Loaded {len(self.notification_history)} notifications from database ({unread_count} unread)")
                
                # Show messagebox for latest unread notification if any
                if unread_count > 0 and latest_unread:
                    notif_type = latest_unread.get('type', '')
                    if notif_type == 'NEW_ANNOUNCEMENT':
                        class_name = latest_unread.get('class_name', 'Unknown Class')
                        announcement_title = latest_unread.get('announcement_title', 'New Announcement')
                        content_preview = latest_unread.get('content_preview', '')
                        
                        msg = f"Class: {class_name}\nAnnouncement: {announcement_title}"
                        if content_preview:
                            msg += f"\n\n{content_preview[:100]}..."
                        
                        if unread_count > 1:
                            msg += f"\n\n(+{unread_count - 1} more unread notification{'s' if unread_count > 2 else ''})"
                        
                        if hasattr(self, 'window') and self.window:
                            self.window.after(100, lambda: messagebox.showinfo("New Announcement", msg))
            elif "materials" in message:
                # Handle VIEW_MATERIALS response
                self.materials = message.get("materials", [])
                print(f"[DEBUG STUDENT] Received materials: count={len(self.materials)}")
                if hasattr(self, 'materials_container') and self.materials_container:
                    print(f"[DEBUG STUDENT] materials_container exists, calling _display_materials")
                    try:
                        self.window.after(0, self._display_materials)
                    except Exception as e:
                        print(f"[DEBUG STUDENT] Error displaying materials: {e}")
                else:
                    print(f"[DEBUG STUDENT] materials_container not available yet")
            elif "assignments" in message:
                # Check if this is for TO-DO page (all assignments) or class-specific assignments
                assignments = message.get("assignments", [])
                
                # If we're on the todo page and assignments have class_name, it's for todo
                if self.current_view == "todo" and assignments and 'class_name' in assignments[0]:
                    print(f"[DEBUG STUDENT] Received all assignments for TO-DO page: count={len(assignments)}")
                    self.window.after(0, lambda: self._display_all_assignments(assignments))
                else:
                    # Handle VIEW_ASSIGNMENTS response for specific class
                    self.assignments = assignments
                    print(f"[DEBUG STUDENT] Received assignments: count={len(self.assignments)}")
                    if hasattr(self, 'assignments_container') and self.assignments_container:
                        print(f"[DEBUG STUDENT] assignments_container exists, calling _display_assignments")
                        try:
                            self.window.after(0, self._display_assignments)
                        except Exception as e:
                            print(f"[DEBUG STUDENT] Error displaying assignments: {e}")
                    else:
                        print(f"[DEBUG STUDENT] assignments_container not available yet")
            elif "submission" in message:
                # Handle GET_STUDENT_SUBMISSION response
                import os
                import subprocess
                
                submission = message.get("submission")
                print(f"[DEBUG] Received submission response: {submission}")
                
                if submission and isinstance(submission, dict):
                    file_path = submission.get('file_path')
                    if file_path and os.path.exists(file_path):
                        try:
                            # Open the file
                            subprocess.run(['open', file_path], check=True)
                            print(f"[DEBUG] Successfully opened file: {file_path}")
                        except Exception as e:
                            print(f"[DEBUG] Error opening file: {e}")
                            self.window.after(0, lambda: messagebox.showerror("Error", f"Could not open file: {str(e)}"))
                    elif file_path:
                        print(f"[DEBUG] File not found: {file_path}")
                        self.window.after(0, lambda: messagebox.showerror("Error", f"Submission file not found at:\n{file_path}"))
                    else:
                        print(f"[DEBUG] No file_path in submission")
                        self.window.after(0, lambda: messagebox.showinfo("No File", "This submission has no file attached"))
                else:
                    print(f"[DEBUG] No submission found or invalid format")
                    # Don't show message here - will be handled by ERROR response
            elif "comments" in message:
                # Handle VIEW_COMMENTS response
                print(f"[DEBUG COMMENTS] Received comments response: {len(message.get('comments', []))} comments")
                if self.current_expand_view:
                    self.current_expand_view.comments = message.get("comments", [])
                    print(f"[DEBUG COMMENTS] Set comments on expand_view, calling _update_comments_display()")
                    self.current_expand_view._update_comments_display()
                else:
                    print(f"[DEBUG COMMENTS] No current_expand_view to update comments")
            elif "comment_id" in message:
                # Handle POST_COMMENT success, refresh comments
                if self.current_expand_view:
                    self.current_expand_view._load_comments()
            elif message.get("message", "").startswith("Successfully joined"):
                # Refresh classes first to show the new class immediately
                self.client.view_classes()
                # Show success message after a brief delay to allow UI update
                self.window.after(100, lambda: messagebox.showinfo("Success", message.get("message")))
        elif msg_type == "NOTIFICATION":
            # Handle real-time TCP notification
            print(f"[DEBUG] Received NOTIFICATION: {message}")
            self._handle_notification(message.get("notification", {}))
        elif msg_type == "ERROR":
            error_msg = message.get("error", "Unknown error")
            print(f"[DEBUG] ERROR message received: {error_msg}")
            # Handle GET_STUDENT_SUBMISSION error when no submission exists
            if error_msg == "No submission found":
                print(f"[DEBUG] Showing 'No submission found' dialog")
                self.window.after(0, lambda: messagebox.showinfo("No Submission", "You haven't submitted this assignment yet"))
            # Don't show connection errors or bad window errors
            elif "connection" not in error_msg.lower() and "bad window" not in error_msg.lower():
                try:
                    if self.window and self.window.winfo_exists():
                        messagebox.showerror("Error", error_msg)
                except:
                    pass  # Window closed, ignore
    
    def _handle_notification(self, notification):
        """Handle incoming real-time notification"""
        from datetime import datetime
        from tkinter import messagebox
    
        print(f"[DEBUG] _handle_notification called with: {notification}")
    
        # Add to notification history
        notification['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.notification_history.insert(0, notification)  # Add to beginning
    
        print(f"[DEBUG] Notification history length: {len(self.notification_history)}")
    
        # Refresh notification page if currently viewing it
        if self.current_view == "notifications":
            self._show_email_notification_page()
    
        notif_type = notification.get('type', '')
    
        if notif_type == 'NEW_ASSIGNMENT':
            class_name = notification.get('class_name', 'Unknown Class')
            assignment_title = notification.get('assignment_title', 'New Assignment')
            due_date = notification.get('due_date', 'No due date')
            class_id = notification.get('class_id')
        
            # CRITICAL FIX: Refresh assignments if viewing that class
            if (self.selected_class and 
                self.selected_class.get('_id') == class_id and
                hasattr(self, 'assignments_container') and 
                self.assignments_container and
                self.assignments_container.winfo_exists()):
            
                print(f"[DEBUG STUDENT] Refreshing assignments for current class after notification")
                # Refresh assignments instantly
                self.client.view_assignments(class_id)
        
            # If currently viewing To-Do page, refresh all assignments
            if self.current_view == "todo":
                print(f"[DEBUG] Refreshing To-Do page for new assignment")
                self.client.send_message('GET_STUDENT_ALL_ASSIGNMENTS', {})
        
            # Show notification popup
            self.window.after(50, lambda: messagebox.showinfo(
                "📚 New Assignment",
                f"Class: {class_name}\n\n"
                f"Assignment: {assignment_title}\n"
                f"Due Date: {due_date}\n\n"
               f"Check your classes to view details."
        ))
        elif notif_type == 'NEW_MATERIAL':
            class_name = notification.get('class_name', 'Unknown Class')
            material_title = notification.get('material_title', 'New Material')
            file_name = notification.get('file_name', 'Unknown file')
            class_id = notification.get('class_id', '')

            print(f"[DEBUG STUDENT] Received NEW_MATERIAL notification for class: {class_id}")

            # MINIMAL FIX: Use same pattern as assignments
            if (self.selected_class and 
                self.selected_class.get('_id') == class_id and
                hasattr(self, 'materials_container') and 
                 self.materials_container and
                self.materials_container.winfo_exists()):
    
                print(f"[DEBUG STUDENT] Refreshing materials for current class")
                     # FIX: Schedule in main thread like assignments do
                if hasattr(self, 'window') and self.window:
                     self.window.after(0, lambda: self.client.view_materials(class_id))
    
            # Show notification popup
            if self.window and self.window.winfo_exists():
                self.window.after(50, lambda: self._show_notification_popup(
                     "📎 New Material",
                     f"Class: {class_name}\n\n"
                     f"Material: {material_title}\n"
                     f"File: {file_name}\n\n"
                     f"Check your classes to download."
                ))
        
        elif notif_type == 'NEW_ANNOUNCEMENT':
            class_name = notification.get('class_name', 'Unknown Class')
            announcement_title = notification.get('announcement_title', 'New Announcement')
            class_id = notification.get('class_id')
        
            # If currently viewing this class's stream, refresh immediately for instant update
            if self.selected_class and self.selected_class.get('_id') == class_id:
                # Cancel any pending refresh for this class
                if class_id in self.pending_refresh:
                    self.window.after_cancel(self.pending_refresh[class_id])
                    del self.pending_refresh[class_id]
            
                # Clear cache to force fresh data
                if class_id in self.announcements_cache:
                   del self.announcements_cache[class_id]
            
            # Refresh immediately (no delay) for instant appearance
                import time
                self.last_refresh_time[class_id] = time.time()
                self.client.view_announcements(class_id)
        
            # Show notification popup (fully async, non-blocking)
            self.window.after(50, lambda: self._show_notification_popup(
                "📢 New Announcement",
                f"Class: {class_name}\n\n{announcement_title}\n\nCheck your classes to view details."
            ))
        
        elif notif_type == 'NEW_MATERIAL':
            class_name = notification.get('class_name', 'Unknown Class')
            material_title = notification.get('material_title', 'New Material')
            file_name = notification.get('file_name', 'Unknown file')
            class_id = notification.get('class_id', '')
        
            # Refresh materials if viewing this class
            if (self.selected_class and 
                self.selected_class.get('_id') == class_id and
                hasattr(self, 'materials_container') and 
                self.materials_container and
                self.materials_container.winfo_exists()):
            
                print(f"[DEBUG] Refreshing materials for current class")
                self.client.view_materials(class_id)
        
             # Show notification popup (fully async)
            self.window.after(50, lambda: self._show_notification_popup(
                "📎 New Material",
                f"Class: {class_name}\n\nMaterial: {material_title}\nFile: {file_name}\n\nCheck your classes to download."
            ))
        
        elif notif_type == 'NEW_COMMENT':
            commenter_name = notification.get('commenter_name', 'Someone')
            item_type = notification.get('item_type', 'item')
            class_name = notification.get('class_name', 'Unknown Class')
            comment_preview = notification.get('comment_preview', '')
            item_id = notification.get('item_id')
            class_id = notification.get('class_id')
        
            print(f"[DEBUG NOTIFICATION] Received NEW_COMMENT: item_id={item_id}, item_type={item_type}")
            print(f"[DEBUG NOTIFICATION] current_expand_view exists: {self.current_expand_view is not None}")
            if self.current_expand_view:
                current_item_id = self.current_expand_view.item_data.get('_id')
                print(f"[DEBUG NOTIFICATION] current_item_id: {current_item_id}")
                print(f"[DEBUG NOTIFICATION] IDs match: {current_item_id == item_id}")
        
            # Show notification popup and refresh comments after user clicks OK
            msg = f"💬 New Comment on {item_type.title()}\n\n"
            msg += f"Class: {class_name}\n"
            msg += f"From: {commenter_name}\n"
            if comment_preview:
                msg += f"Comment: {comment_preview[:50]}{'...' if len(comment_preview) > 50 else ''}\n\n"
            msg += "Check your classes to view and reply."
        
            # Check if currently viewing the expanded item
            should_refresh_comments = (self.current_expand_view and 
                self.current_expand_view.item_data.get('_id') == item_id)
        
            print(f"[DEBUG NOTIFICATION] should_refresh_comments: {should_refresh_comments}")
        
            if should_refresh_comments:
                print(f"[DEBUG] Will refresh comments after notification popup is dismissed")
                # Schedule popup with callback to refresh comments after dismissal
                self.window.after(50, lambda: self._show_comment_notification_and_refresh(msg, item_type))
            else:
                # Just show popup without refreshing
                self.window.after(50, lambda: self._show_notification_popup("💬 New Comment", msg))
    
        # Refresh notification page if currently viewing it
        if self.current_view == "notifications":
            self._show_email_notification_page()
    
    def _debounced_refresh(self, class_id):
        """Debounced refresh to batch multiple notification updates"""
        # Clean up pending refresh
        if class_id in self.pending_refresh:
            del self.pending_refresh[class_id]
        
        # Only refresh if window exists and still viewing this class
        try:
            if (self.window and self.window.winfo_exists() and 
                self.selected_class and self.selected_class.get('_id') == class_id):
                import time
                self.last_refresh_time[class_id] = time.time()
                self.client.view_announcements(class_id)
        except:
            pass  # Window closed or invalid
    
    def _show_notification_popup(self, title, message):
        """Show notification popup in a non-blocking way"""
        try:
            # Check if window still exists and is valid
            if self.window and self.window.winfo_exists():
                messagebox.showinfo(title, message)
        except Exception as e:
            # Silently ignore errors (window closed, bad window path, etc.)
            pass
    
    def _show_comment_notification_and_refresh(self, message, item_type):
        """Show comment notification popup and refresh comments after dismissal"""
        try:
            # Check if window still exists and is valid
            if self.window and self.window.winfo_exists():
                print(f"[DEBUG] Showing comment notification popup for {item_type}")
                messagebox.showinfo("💬 New Comment", message)
                # After popup is dismissed, refresh comments
                print(f"[DEBUG] Popup dismissed, now refreshing comments for {item_type}")
                if self.current_expand_view:
                    print(f"[DEBUG] Calling _load_comments() on current_expand_view")
                    self.current_expand_view._load_comments()
                else:
                    print(f"[DEBUG] No current_expand_view to refresh comments")
        except Exception as e:
            # Silently ignore errors (window closed, bad window path, etc.)
            print(f"[DEBUG] Error in _show_comment_notification_and_refresh: {e}")
            pass
    
    def _show_todo_page(self):
        """Show To-Do page with all assignments from all classes"""
        self.current_view = "todo"
        
        # Clear main content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # To-Do page header
        header = ttk.Frame(self.content_frame, bootstyle="dark")
        header.pack(fill=X, padx=40, pady=20)

        
        ttk.Label(
            header,
            text="📝 To-Do - All Assignments",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W)
        
        ttk.Label(
            header,
            text="View all your assignments across all classes",
            font=("Arial", 12),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(5, 0))
        
        # Loading message
        ttk.Label(
            self.content_frame,
            text="📥 Loading assignments...",
            font=("Arial", 14),
            bootstyle="secondary"
        ).pack(pady=50)
        
        # Request all assignments from server
        self.client.send_message('GET_STUDENT_ALL_ASSIGNMENTS', {})
    
    def _display_all_assignments(self, assignments):
        """Display all assignments in To-Do page"""
        if self.current_view != "todo":
            return
        
        # Clear loading message
        for widget in self.content_frame.winfo_children():
            if widget.winfo_class() == 'TLabel' and 'Loading' in str(widget.cget('text')):
                widget.destroy()
        
        if not assignments:
            ttk.Label(
                self.content_frame,
                text="📭 No assignments yet",
                font=("Arial", 16),
                bootstyle="secondary"
            ).pack(pady=50)
            ttk.Label(
                self.content_frame,
                text="Your assignments will appear here when teachers create them",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack()
            return
        
        # Canvas for scrolling
        from tkinter import Canvas, Scrollbar, LEFT, RIGHT, BOTH, YES, Y, NW
        canvas = Canvas(self.content_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, bootstyle="dark")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind(
         "<Configure>",
          lambda e: canvas.itemconfig(window_id, width=e.width)
       )

        # Assignments list
        list_frame = ttk.Frame(scrollable_frame, bootstyle="dark")
        list_frame.pack(fill=BOTH, expand=YES, padx=30, pady=10)
        
        for assignment in assignments:
            self._create_todo_assignment_card(list_frame, assignment).pack(fill=X, pady=8)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _create_todo_assignment_card(self, parent, assignment):
        """Create an assignment card for the To-Do page"""
        card = ttk.Frame(parent, bootstyle="secondary", relief="raised")
        card.configure(padding=15)
        
        # Top row: Title and class name
        top_row = ttk.Frame(card, bootstyle="secondary")
        top_row.pack(fill=X)
        
        ttk.Label(
            top_row,
            text=f"📚 {assignment.get('title', 'Untitled')}",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT)
        
        # Class name badge
        class_badge = ttk.Frame(top_row, bootstyle="info")
        class_badge.pack(side=RIGHT, padx=5)
        ttk.Label(
            class_badge,
            text=assignment.get('class_name', 'Unknown'),
            font=("Arial", 10),
            bootstyle="inverse-info",
            padding=(8, 4)
        ).pack()
        
        # Description
        if assignment.get('description'):
            ttk.Label(
                card,
                text=assignment['description'],
                font=("Arial", 11),
                bootstyle="inverse-secondary",
                wraplength=700
            ).pack(anchor=W, pady=(10, 5))
        
        # Bottom row: Due date, points, and status
        bottom_row = ttk.Frame(card, bootstyle="secondary")
        bottom_row.pack(fill=X, pady=(10, 0))
        
        # Due date
        due_date = assignment.get('due_date', 'No due date')
        ttk.Label(
            bottom_row,
            text=f"📅 Due: {due_date}",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=(0, 20))
        
        # Max points
        max_points = assignment.get('max_points', 100)
        ttk.Label(
            bottom_row,
            text=f"💯 {max_points} points",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=(0, 20))
        
        # Submission status
        if assignment.get('submitted'):
            status_badge = ttk.Frame(bottom_row, bootstyle="success")
            status_badge.pack(side=RIGHT)
            ttk.Label(
                status_badge,
                text="✓ Submitted",
                font=("Arial", 10, "bold"),
                bootstyle="inverse-success",
                padding=(8, 4)
            ).pack()
        else:
            status_badge = ttk.Frame(bottom_row, bootstyle="warning")
            status_badge.pack(side=RIGHT)
            ttk.Label(
                status_badge,
                text="⏳ Not Submitted",
                font=("Arial", 10, "bold"),
                bootstyle="inverse-warning",
                padding=(8, 4)
            ).pack()
        
        return card
    
    def _show_email_notification_page(self):
        """Show Email Notification page"""
        self.current_view = "notifications"
        
        # Clear main content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Email notification page content
        header = ttk.Frame(self.content_frame, bootstyle="dark")
        header.pack(fill=X, padx=40, pady=20)
        
        ttk.Label(
            header,
            text="🔔 Notifications",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-light"
        ).pack(side=LEFT)
        
        # Content area
        content = ttk.Frame(self.content_frame, bootstyle="dark")
        content.pack(fill=BOTH, expand=YES, padx=40, pady=20)
        
        # Info section
        info_frame = ttk.Frame(content, bootstyle="dark")
        info_frame.pack(fill=X, pady=(0, 30))
        
        ttk.Label(
            info_frame,
            text="📬 Notification Settings",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, pady=(0, 10))
        
        ttk.Label(
            info_frame,
            text="You will receive email notifications for:",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        # Notification types in compact format
        ttk.Label(
            info_frame,
            text="• Announcements  • Assignments  • Materials  • Comments  • Deadlines   ",
            font=("Arial", 10),
            bootstyle="inverse-secondary"
        ).pack(anchor=W, pady=2, padx=20)
        
        # Current email display
        email_frame = ttk.Frame(content, bootstyle="dark")
        email_frame.pack(fill=X, pady=(15, 0))
        
        ttk.Label(
            email_frame,
            text="✉️ Notifications sent to:",
            font=("Arial", 11, "bold"),
            bootstyle="inverse-light"
        ).pack(anchor=W, pady=(0, 5))
        
        ttk.Label(
            email_frame,
            text=self.user_data.get('email', 'Not available'),
            font=("Arial", 12),
            bootstyle="inverse-info"
        ).pack(anchor=W, padx=20)
        
        # Notification History section
        ttk.Separator(content, orient=HORIZONTAL).pack(fill=X, pady=20)
        
        history_header = ttk.Frame(content, bootstyle="dark")
        history_header.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            history_header,
            text="📋 Recent Notifications",
            font=("Arial", 16, "bold"),
            bootstyle="inverse-light"
        ).pack(side=LEFT)
        
        ttk.Label(
            history_header,
            text=f"({len(self.notification_history)} total)",
            font=("Arial", 11),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=10)
        
        # Notification list
        if not self.notification_history:
            ttk.Label(
                content,
                text="No notifications yet",
                font=("Arial", 12),
                bootstyle="inverse-secondary"
            ).pack(pady=20)
        else:
            # Create scrollable frame for notifications
            notif_canvas = Canvas(content, bg="#222", highlightthickness=0, height=250)
            notif_scrollbar = ttk.Scrollbar(content, orient=VERTICAL, command=notif_canvas.yview)
            notif_frame = ttk.Frame(notif_canvas, bootstyle="dark")
            
            notif_frame.bind("<Configure>", lambda e: notif_canvas.configure(scrollregion=notif_canvas.bbox("all")))
            window_id = notif_canvas.create_window((0, 0), window=notif_frame, anchor=NW)
            notif_canvas.configure(yscrollcommand=notif_scrollbar.set)
            notif_canvas.bind(
              "<Configure>",
                lambda e: notif_canvas.itemconfig(window_id, width=e.width)
                )

            
            # Display notifications
            for notif in self.notification_history[:20]:  # Show last 20
                notif_card = ttk.Frame(notif_frame, bootstyle="secondary", padding=15)
                notif_card.pack(fill=X, pady=5, padx=5)
                
                # Icon and title based on type
                notif_type = notif.get('type', '')
                if notif_type == 'NEW_ASSIGNMENT':
                    icon = "📚"
                    title = f"New Assignment: {notif.get('assignment_title', 'Unknown')}"
                    details = f"Class: {notif.get('class_name', 'Unknown')}\nDue: {notif.get('due_date', 'No date')}"
                elif notif_type == 'NEW_ANNOUNCEMENT':
                    icon = "📢"
                    title = f"New Announcement: {notif.get('announcement_title', 'Unknown')}"
                    details = f"Class: {notif.get('class_name', 'Unknown')}"
                elif notif_type == 'NEW_MATERIAL':
                    icon = "📎"
                    title = f"New Material: {notif.get('material_title', 'Unknown')}"
                    details = f"Class: {notif.get('class_name', 'Unknown')}\nFile: {notif.get('file_name', 'Unknown')}"
                elif notif_type == 'NEW_COMMENT':
                    icon = "💬"
                    title = f"New Comment from {notif.get('commenter_name', 'Unknown')}"
                    details = f"On: {notif.get('announcement_title', 'Unknown')}"
                else:
                    icon = "🔔"
                    title = "Notification"
                    details = ""
                
                # Title row
                title_frame = ttk.Frame(notif_card, bootstyle="secondary")
                title_frame.pack(fill=X)
                
                ttk.Label(
                    title_frame,
                    text=f"{icon}  {title}",
                    font=("Arial", 11, "bold"),
                    bootstyle="inverse-light"
                ).pack(side=LEFT)
                
                ttk.Label(
                    title_frame,
                    text=notif.get('received_at', ''),
                    font=("Arial", 9),
                    bootstyle="inverse-secondary"
                ).pack(side=RIGHT)
                
                # Details
                if details:
                    ttk.Label(
                        notif_card,
                        text=details,
                        font=("Arial", 10),
                        bootstyle="inverse-secondary"
                    ).pack(anchor=W, pady=(5, 0))
            
            notif_canvas.pack(side=LEFT, fill=BOTH, expand=YES)
            notif_scrollbar.pack(side=RIGHT, fill=Y)
        
        
        self.current_view = "notifications"
    
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
                    from client.teacher_dashboard import TeacherDashboard
                    dashboard = TeacherDashboard(new_client, user_data)
                    dashboard.show()
                else:
                    dashboard = StudentDashboard(new_client, user_data)
                    dashboard.show()
            
            login = LoginWindow(new_client, on_login_success)
            login.show()
    
    def _on_closing(self):
        """Handle closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.client.disconnect()
            self.window.destroy()

    def _save_downloaded_file(self, filename, binary_data, request_id=None):
        """Save a downloaded file"""
        print(f"[DEBUG STUDENT SAVE] _save_downloaded_file called: {filename}, data size: {len(binary_data) if binary_data else 0}")
    
        from tkinter import filedialog, messagebox
    
        try:
            # CRITICAL: Validate binary data
            if not binary_data:
                print(f"[ERROR STUDENT SAVE] No binary data received")
                messagebox.showerror("Error", "No file data received")
                return
        
            if not isinstance(binary_data, bytes):
                print(f"[ERROR STUDENT SAVE] Binary data is not bytes, type: {type(binary_data)}")
                messagebox.showerror("Error", "File data is corrupted")
                return
        
            print(f"[DEBUG STUDENT SAVE] Showing save dialog for: {filename}")
        
            # Ask user where to save
            save_path = filedialog.asksaveasfilename(
                defaultextension="",
                initialfile=filename,
                filetypes=[("All Files", "*.*")]
            )
        
            print(f"[DEBUG STUDENT SAVE] User selected path: {save_path}")
        
            if save_path:
                # Save the file
                with open(save_path, 'wb') as f:
                    f.write(binary_data)
            
                print(f"[DEBUG STUDENT SAVE] File saved successfully: {save_path}")
            
                messagebox.showinfo(
                    "Success", 
                    f"✅ File saved successfully!\n\n"
                    f"📄 {filename}\n"
                    f"📦 Size: {len(binary_data):,} bytes\n"
                    f"📁 Location: {save_path}"
                )
            else:
               print(f"[DEBUG STUDENT SAVE] User cancelled save")
               messagebox.showinfo("Cancelled", "Download cancelled")
            
        except Exception as e:
            print(f"[ERROR STUDENT SAVE] Exception: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Cannot save file: {str(e)}")

    def _open_downloaded_file(self, filename, binary_data, request_id=None):
        """Open a downloaded file directly"""
        print(f"[DEBUG STUDENT OPEN] _open_downloaded_file called: {filename}, data size: {len(binary_data) if binary_data else 0}")
    
        from tkinter import messagebox
        import tempfile
        import os
        import subprocess
        import sys
    
        try:
            # CRITICAL: Validate binary data
            if not binary_data:
                print(f"[ERROR STUDENT OPEN] No binary data received")
                messagebox.showerror("Error", "No file data received")
                return
        
            if not isinstance(binary_data, bytes):
                print(f"[ERROR STUDENT OPEN] Binary data is not bytes, type: {type(binary_data)}")
                messagebox.showerror("Error", "File data is corrupted")
                return
        
            # Make sure filename is a string
            if not isinstance(filename, str):
                filename = str(filename) if filename else "download.bin"
        
            # Create temp file
            import tempfile
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=os.path.splitext(filename)[1] or '.bin',
                prefix='download_'
            ) as tmp:
                tmp.write(binary_data)
                temp_path = tmp.name
        
            print(f"[DEBUG STUDENT OPEN] Saved temp file: {temp_path}")
        
            # Open the file with default application
            try:
               if os.name == 'nt':  # Windows
                    os.startfile(temp_path)
                    message = f"✅ Opening file: {filename}"
               elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', temp_path], check=True)
                    message = f"✅ Opening file: {filename}"
               else:  # Linux
                    subprocess.run(['xdg-open', temp_path], check=True)
                    message = f"✅ Opening file: {filename}"
            
               messagebox.showinfo(
                    "Success", 
                    f"{message}\n\n"
                   f"📄 {filename}\n"
                    f"📦 Size: {len(binary_data):,} bytes\n"
                    f"📁 Temporary file: {temp_path}"
                )
            
            except Exception as open_error:
                print(f"[DEBUG STUDENT OPEN] Could not open directly: {open_error}")
                messagebox.showinfo(
                    "File Saved", 
                    f"📄 {filename}\n"
                    f"📦 Size: {len(binary_data):,} bytes\n"
                    f"📁 Saved to temporary location:\n{temp_path}\n\n"
                    f"Please open it manually from this location."
                )
        
        except Exception as e:
            print(f"[ERROR STUDENT OPEN] Exception: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Cannot open file: {str(e)}")

    def _refresh_current_class_view(self):
        """Refresh all data for the currently selected class"""
        if not self.selected_class:
            return
    
        class_id = self.selected_class['_id']
        print(f"[DEBUG] Refreshing all data for class: {class_id}")
    
        # Refresh announcements
        if hasattr(self, 'stream_container'):
            self.client.view_announcements(class_id)
    
        # Refresh assignments if assignments tab exists
        if (hasattr(self, 'assignments_container') and 
            self.assignments_container and
            self.assignments_container.winfo_exists()):
            self.client.view_assignments(class_id)
     
        # Refresh materials if materials tab exists
        if (hasattr(self, 'materials_container') and 
            self.materials_container and
            self.materials_container.winfo_exists()):
            self.client.view_materials(class_id)