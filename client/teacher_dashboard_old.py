import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import LearnLiveClient

class TeacherDashboard:
    """
    Teacher Dashboard for LearnLive.
    Provides all teacher features in a modern UI.
    """
    
    def __init__(self, client: LearnLiveClient, user_data: dict):
        """
        Initialize teacher dashboard.
        
        Args:
            client: LearnLiveClient instance
            user_data: User information
        """
        self.client = client
        self.user_data = user_data
        self.window = None
        self.classes = []
        self.selected_class = None
        
        # Setup message callback
        self.client.set_message_callback(self._handle_server_message)
    
    def show(self):
        """Show the teacher dashboard."""
        self.window = ttk.Window(themename="cosmo")
        self.window.title(f"LearnLive - Teacher Dashboard - {self.user_data.get('name', 'Teacher')}")
        self.window.geometry("1200x800")
        
        # Setup window close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=BOTH, expand=YES)
        
        # Top navigation bar
        self._create_navbar(main_container)
        
        # Content area with sidebar
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=BOTH, expand=YES)
        
        # Left sidebar (class list)
        self._create_sidebar(content_frame)
        
        # Right content area
        self.content_area = ttk.Frame(content_frame, padding=20)
        self.content_area.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # Show welcome screen
        self._show_welcome_screen()
        
        # Load classes
        self.client.view_classes()
        
        self.window.mainloop()
    
    def _create_navbar(self, parent):
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
            text=f"👨‍🏫 {self.user_data.get('name', 'Teacher')}",
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
        
        # Create class button
        create_btn = ttk.Button(
            header_frame,
            text="➕ Create Class",
            command=self._show_create_class_dialog,
            bootstyle="success",
            width=20
        )
        create_btn.pack(pady=(10, 0))
        
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
            text=f"Welcome, {self.user_data.get('name', 'Teacher')}! 👋",
            font=("Arial", 24, "bold"),
            bootstyle="primary"
        )
        welcome_label.pack(pady=20)
        
        info_label = ttk.Label(
            welcome_frame,
            text="Create a class or select one from the sidebar to get started",
            font=("Arial", 14),
            bootstyle="secondary"
        )
        info_label.pack()
    
    def _show_create_class_dialog(self):
        """Show dialog to create new class."""
        dialog = ttk.Toplevel(self.window)
        dialog.title("Create New Class")
        dialog.geometry("500x400")
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
        
        # Class name
        ttk.Label(form_frame, text="Class Name*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        name_entry = ttk.Entry(form_frame, font=("Arial", 12), width=40)
        name_entry.pack(fill=X, pady=(0, 15))
        
        # Subject
        ttk.Label(form_frame, text="Subject*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        subject_entry = ttk.Entry(form_frame, font=("Arial", 12), width=40)
        subject_entry.pack(fill=X, pady=(0, 15))
        
        # Description
        ttk.Label(form_frame, text="Description", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        desc_text = ttk.Text(form_frame, height=6, font=("Arial", 11))
        desc_text.pack(fill=BOTH, expand=YES, pady=(0, 20))
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_create():
            class_name = name_entry.get().strip()
            subject = subject_entry.get().strip()
            description = desc_text.get("1.0", END).strip()
            
            if not class_name or not subject:
                messagebox.showerror("Error", "Please fill required fields")
                return
            
            self.client.create_class(class_name, description, subject)
            dialog.destroy()
        
        ttk.Button(
            btn_frame,
            text="Create",
            command=handle_create,
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
            text=f"📚 {self.selected_class.get('subject', '')} | Class Code: {self.selected_class.get('class_code', '')}",
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
        
        # Students tab
        students_frame = ttk.Frame(notebook, padding=20)
        notebook.add(students_frame, text="Students")
        self._create_students_tab(students_frame)
    
    def _create_stream_tab(self, parent):
        """Create stream/announcements tab."""
        # Post announcement button
        ttk.Button(
            parent,
            text="➕ Post Announcement",
            command=self._show_post_announcement_dialog,
            bootstyle="primary",
            width=20
        ).pack(anchor=W, pady=(0, 20))
        
        # Announcements list
        self.announcements_frame = ttk.Frame(parent)
        self.announcements_frame.pack(fill=BOTH, expand=YES)
        
        # Load announcements
        self.client.view_announcements(str(self.selected_class["_id"]))
    
    def _create_assignments_tab(self, parent):
        """Create assignments tab."""
        # Create assignment button
        ttk.Button(
            parent,
            text="➕ Create Assignment",
            command=self._show_create_assignment_dialog,
            bootstyle="success",
            width=20
        ).pack(anchor=W, pady=(0, 20))
        
        # Assignments list
        self.assignments_frame = ttk.Frame(parent)
        self.assignments_frame.pack(fill=BOTH, expand=YES)
        
        # Load assignments
        self.client.view_assignments(str(self.selected_class["_id"]))
    
    def _create_materials_tab(self, parent):
        """Create materials tab."""
        # Upload material button
        ttk.Button(
            parent,
            text="➕ Upload Material",
            command=self._show_upload_material_dialog,
            bootstyle="info",
            width=20
        ).pack(anchor=W, pady=(0, 20))
        
        # Materials list
        self.materials_frame = ttk.Frame(parent)
        self.materials_frame.pack(fill=BOTH, expand=YES)
        
        # Load materials
        self.client.view_materials(str(self.selected_class["_id"]))
    
    def _create_students_tab(self, parent):
        """Create students tab."""
        # Student count
        self.students_count_label = ttk.Label(
            parent,
            text="Loading students...",
            font=("Arial", 12),
            bootstyle="secondary"
        )
        self.students_count_label.pack(anchor=W, pady=(0, 20))
        
        # Students list
        self.students_listbox = ttk.Treeview(
            parent,
            columns=("name", "email"),
            show="headings",
            height=15
        )
        self.students_listbox.heading("name", text="Name")
        self.students_listbox.heading("email", text="Email")
        self.students_listbox.column("name", width=250)
        self.students_listbox.column("email", width=300)
        self.students_listbox.pack(fill=BOTH, expand=YES)
        
        # Context menu
        self.students_listbox.bind("<Button-2>", self._show_student_context_menu)  # Right-click on macOS
        self.students_listbox.bind("<Button-3>", self._show_student_context_menu)  # Right-click on Windows/Linux
        
        # Load students
        self.client.view_students(str(self.selected_class["_id"]))
    
    def _show_post_announcement_dialog(self):
        """Show dialog to post announcement."""
        dialog = ttk.Toplevel(self.window)
        dialog.title("Post Announcement")
        dialog.geometry("600x400")
        dialog.transient(self.window)
        dialog.grab_set()
        
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(form_frame, text="Title*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        title_entry = ttk.Entry(form_frame, font=("Arial", 12), width=50)
        title_entry.pack(fill=X, pady=(0, 15))
        
        # Content
        ttk.Label(form_frame, text="Content*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        content_text = ttk.Text(form_frame, height=10, font=("Arial", 11))
        content_text.pack(fill=BOTH, expand=YES, pady=(0, 20))
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_post():
            title = title_entry.get().strip()
            content = content_text.get("1.0", END).strip()
            
            if not title or not content:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            self.client.post_announcement(str(self.selected_class["_id"]), title, content)
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Post", command=handle_post, bootstyle="primary", width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary", width=15).pack(side=LEFT, padx=5)
    
    def _show_create_assignment_dialog(self):
        """Show dialog to create assignment."""
        dialog = ttk.Toplevel(self.window)
        dialog.title("Create Assignment")
        dialog.geometry("600x500")
        dialog.transient(self.window)
        dialog.grab_set()
        
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        # Title
        ttk.Label(form_frame, text="Title*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        title_entry = ttk.Entry(form_frame, font=("Arial", 12), width=50)
        title_entry.pack(fill=X, pady=(0, 15))
        
        # Description
        ttk.Label(form_frame, text="Description*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        desc_text = ttk.Text(form_frame, height=8, font=("Arial", 11))
        desc_text.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        # Due date
        ttk.Label(form_frame, text="Due Date*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        due_entry = ttk.Entry(form_frame, font=("Arial", 12), width=30)
        due_entry.insert(0, "YYYY-MM-DD")
        due_entry.pack(anchor=W, pady=(0, 15))
        
        # Max points
        ttk.Label(form_frame, text="Max Points*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        points_entry = ttk.Entry(form_frame, font=("Arial", 12), width=20)
        points_entry.insert(0, "100")
        points_entry.pack(anchor=W, pady=(0, 20))
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_create():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", END).strip()
            due_date = due_entry.get().strip()
            max_points = points_entry.get().strip()
            
            if not title or not description or not due_date or not max_points:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                max_points = int(max_points)
            except ValueError:
                messagebox.showerror("Error", "Max points must be a number")
                return
            
            self.client.create_assignment(
                str(self.selected_class["_id"]),
                title,
                description,
                due_date,
                max_points
            )
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Create", command=handle_create, bootstyle="success", width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary", width=15).pack(side=LEFT, padx=5)
    
    def _show_upload_material_dialog(self):
        """Show dialog to upload material."""
        file_path = filedialog.askopenfilename(
            title="Select Material File",
            filetypes=[
                ("All Files", "*.*"),
                ("PDF Files", "*.pdf"),
                ("Documents", "*.doc *.docx"),
                ("Images", "*.png *.jpg *.jpeg")
            ]
        )
        
        if not file_path:
            return
        
        # Get material name
        dialog = ttk.Toplevel(self.window)
        dialog.title("Upload Material")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()
        
        form_frame = ttk.Frame(dialog, padding=30)
        form_frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(form_frame, text="Material Name*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        name_entry = ttk.Entry(form_frame, font=("Arial", 12), width=35)
        name_entry.insert(0, os.path.basename(file_path))
        name_entry.pack(fill=X, pady=(0, 15))
        
        ttk.Label(form_frame, text="Type*", font=("Arial", 11)).pack(anchor=W, pady=(0, 5))
        type_var = ttk.StringVar(value="document")
        type_combo = ttk.Combobox(form_frame, textvariable=type_var, values=["document", "image", "pdf", "other"], state="readonly")
        type_combo.pack(anchor=W, pady=(0, 20))
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack()
        
        def handle_upload():
            name = name_entry.get().strip()
            mat_type = type_var.get()
            
            if not name:
                messagebox.showerror("Error", "Please enter material name")
                return
            
            self.client.upload_material(
                str(self.selected_class["_id"]),
                name,
                mat_type,
                file_path
            )
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Upload", command=handle_upload, bootstyle="info", width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary", width=15).pack(side=LEFT, padx=5)
    
    def _show_student_context_menu(self, event):
        """Show context menu for student."""
        # Get selected student
        item = self.students_listbox.identify_row(event.y)
        if not item:
            return
        
        self.students_listbox.selection_set(item)
        student_id = self.students_listbox.item(item)["tags"][0] if self.students_listbox.item(item)["tags"] else None
        
        if not student_id:
            return
        
        # Create context menu
        menu = ttk.Menu(self.window)
        menu.add_command(
            label="Remove from Class",
            command=lambda: self._remove_student(student_id)
        )
        
        # Show menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _remove_student(self, student_id: str):
        """Remove student from class."""
        if messagebox.askyesno("Confirm", "Are you sure you want to remove this student?"):
            self.client.remove_student(str(self.selected_class["_id"]), student_id)
    
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
                self._display_students(data["students"])
            
            # Show success message for actions
            action_msg = message.get("message", "")
            if action_msg and action_msg not in ["Success", "OK"]:
                messagebox.showinfo("Success", action_msg)
                
                # Refresh current view
                if self.selected_class:
                    if "class" in action_msg.lower():
                        self.client.view_classes()
                    elif "announcement" in action_msg.lower():
                        self.client.view_announcements(str(self.selected_class["_id"]))
                    elif "assignment" in action_msg.lower():
                        self.client.view_assignments(str(self.selected_class["_id"]))
                    elif "material" in action_msg.lower():
                        self.client.view_materials(str(self.selected_class["_id"]))
                    elif "student" in action_msg.lower():
                        self.client.view_students(str(self.selected_class["_id"]))
        
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
        created_at = announcement.get("created_at", "")
        ttk.Label(
            inner,
            text=f"Posted on {created_at}",
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
        
        # Comments link
        ttk.Button(
            inner,
            text="View Comments",
            command=lambda: self._view_comments(announcement),
            bootstyle="link"
        ).pack(anchor=W)
    
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
        
        for assignment in assignments:
            self._create_assignment_card(self.assignments_frame, assignment)
    
    def _create_assignment_card(self, parent, assignment: dict):
        """Create assignment card widget."""
        card = ttk.Frame(parent, bootstyle="info", relief="solid", borderwidth=1)
        card.pack(fill=X, pady=(0, 15))
        
        inner = ttk.Frame(card, padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        # Title and points
        header = ttk.Frame(inner)
        header.pack(fill=X)
        
        ttk.Label(
            header,
            text=assignment.get("title", "Assignment"),
            font=("Arial", 14, "bold")
        ).pack(side=LEFT)
        
        ttk.Label(
            header,
            text=f"{assignment.get('max_points', 0)} points",
            font=("Arial", 12),
            bootstyle="info"
        ).pack(side=RIGHT)
        
        # Due date
        ttk.Label(
            inner,
            text=f"Due: {assignment.get('due_date', 'N/A')}",
            font=("Arial", 10),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(5, 10))
        
        # Description
        ttk.Label(
            inner,
            text=assignment.get("description", ""),
            font=("Arial", 11),
            wraplength=700
        ).pack(anchor=W, pady=(0, 10))
        
        # View submissions button
        ttk.Button(
            inner,
            text="View Submissions",
            command=lambda: self._view_submissions(assignment),
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
                text="No materials uploaded yet",
                font=("Arial", 12),
                bootstyle="secondary"
            ).pack(pady=20)
            return
        
        # Create grid of materials
        for i, material in enumerate(materials):
            self._create_material_card(self.materials_frame, material, i)
    
    def _create_material_card(self, parent, material: dict, index: int):
        """Create material card widget."""
        card = ttk.Frame(parent, bootstyle="light", relief="solid", borderwidth=1)
        card.pack(fill=X, pady=(0, 10))
        
        inner = ttk.Frame(card, padding=10)
        inner.pack(fill=BOTH, expand=YES)
        
        # Icon based on type
        mat_type = material.get("material_type", "document")
        icon = "📄" if mat_type == "document" else "🖼️" if mat_type == "image" else "📕"
        
        ttk.Label(
            inner,
            text=f"{icon} {material.get('material_name', 'Material')}",
            font=("Arial", 12, "bold")
        ).pack(side=LEFT)
        
        ttk.Label(
            inner,
            text=f"Uploaded: {material.get('uploaded_at', '')}",
            font=("Arial", 9),
            bootstyle="secondary"
        ).pack(side=RIGHT)
    
    def _display_students(self, students: list):
        """Display students list."""
        self.students_listbox.delete(*self.students_listbox.get_children())
        
        self.students_count_label.config(text=f"Total Students: {len(students)}")
        
        for student in students:
            student_id = str(student["_id"])
            name = student.get("name", "Unknown")
            email = student.get("email", "")
            
            self.students_listbox.insert(
                "",
                END,
                values=(name, email),
                tags=(student_id,)
            )
    
    def _view_comments(self, announcement: dict):
        """View comments on announcement."""
        # TODO: Implement comments view dialog
        messagebox.showinfo("Comments", "Comments feature coming soon!")
    
    def _view_submissions(self, assignment: dict):
        """View assignment submissions."""
        self.client.view_submissions(str(assignment["_id"]))
        # TODO: Show submissions in dialog
        messagebox.showinfo("Submissions", "Viewing submissions...")
    
    def _handle_logout(self):
        """Handle logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
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
    
    def _on_closing(self):
        """Handle window close."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.client.disconnect()
            self.window.destroy()
