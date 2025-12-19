import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import os
import sys
import tkinter as tk

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.utility import LearnLiveClient


class ExpandView:
    """Expanded view for announcements, assignments, and materials"""

    def __init__(self, dashboard, item_type, item_data):
        self.dashboard = dashboard
        self.item_type = item_type
        self.item_data = item_data
        self.comment_visible = False
        self.comment_text = None
        self.comment_button = None
        self.comments = []

    def show(self):
      """Show the expanded view (FIXED)"""

    # Hide main content frame
      self.dashboard.content_frame.pack_forget()
      self.dashboard.content_frame.update_idletasks()

    # Correct parent (VERY IMPORTANT)
      parent = self.dashboard.content_frame.master

    # Expanded container (use tk.Frame for background)
      self.expanded_frame = tk.Frame(parent, bg="#222222")
      self.expanded_frame.pack(fill=BOTH, expand=YES)

    # Back button area
      back_frame = tk.Frame(self.expanded_frame, bg="#222222")
      back_frame.pack(fill=X, padx=20, pady=10)

      ttk.Button(
        back_frame,
        text="← Back",
        command=self._back_to_main,
        bootstyle="secondary"
      ).pack(side=LEFT)

    # Main content area
      content_area = tk.Frame(self.expanded_frame, bg="#222222")
      content_area.pack(fill=BOTH, expand=YES, padx=20, pady=20)

    # Render content
      if self.item_type == 'announcement':
        self._display_announcement(content_area)
      elif self.item_type == 'assignment':
        self._display_assignment(content_area)
      elif self.item_type == 'material':
        self._display_material(content_area)


    def _display_announcement(self, parent):
        """Display expanded announcement"""
        # Title
        tk.Label(
            parent,
            text=self.item_data.get('title', 'Announcement'),
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#222222"
        ).pack(anchor=W, pady=(0, 10))

        # Content
        tk.Label(
            parent,
            text=self.item_data.get('content', ''),
            font=("Arial", 12),
            fg="white",
            bg="#222222",
            wraplength=800,
            justify=LEFT
        ).pack(anchor=W, pady=(0, 10))

        # Date
        date_str = self.item_data.get('created_at', '')
        if date_str:
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_date = date_str

            tk.Label(
                parent,
                text=f"Posted: {formatted_date}",
                font=("Arial", 10),
                fg="#cccccc",
                bg="#222222"
            ).pack(anchor=W, pady=(0, 20))

        # Load and display comments
        self._load_comments()
        self._display_comments(parent)

        # Comment section
        self._add_comment_section(parent)
    def _load_comments(self):
        """Load comments for this item"""
        item_id = self.item_data.get('_id')
        print(f"[DEBUG EXPAND] _load_comments called for item_id={item_id}, item_type={self.item_type}")
        self.dashboard.client.view_comments(item_id, self.item_type)
    def _display_assignment(self, parent):
        """Display expanded assignment"""
        # Title
        tk.Label(
            parent,
            text=f"📝 {self.item_data.get('title', 'Assignment')}",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#222222"
        ).pack(anchor=W, pady=(0, 10))

        # Description
        description = self.item_data.get('description', '')
        if description:
            tk.Label(
                parent,
                text=description,
                font=("Arial", 12),
                fg="white",
                bg="#222222",
                wraplength=800,
                justify=LEFT
            ).pack(anchor=W, pady=(0, 10))

        # Details
        details_frame = tk.Frame(parent, bg="#222222")
        details_frame.pack(fill=X, pady=(0, 20))

        due_date = self.item_data.get('due_date', 'No due date')
        tk.Label(
            details_frame,
            text=f"📅 Due: {due_date}",
            font=("Arial", 11),
            fg="#cccccc",
            bg="#222222"
        ).pack(side=LEFT, padx=(0, 30))

        max_points = self.item_data.get('max_points', 100)
        tk.Label(
            details_frame,
            text=f"💯 Points: {max_points}",
            font=("Arial", 11),
            fg="#cccccc",
            bg="#222222"
        ).pack(side=LEFT)

        # Upload button (existing functionality)
        def upload_submission():
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select file to submit",
                filetypes=[
                    ("All Files", "*.*"),
                    ("PDF Files", "*.pdf"),
                    ("Word Documents", "*.docx"),
                    ("Text Files", "*.txt")
                ]
            )
            if file_path:
                result = self.dashboard.client.submit_assignment(
                    self.item_data.get('_id'),
                    "",  # submission_text
                    file_path
                )
                if result:
                    messagebox.showinfo("Success", "Assignment submitted successfully!")
                else:
                    messagebox.showerror("Error", "Failed to submit assignment")

        upload_btn = ttk.Button(
            parent,
            text="📤 Upload assignment",
            command=upload_submission,
            bootstyle="success"
        )
        upload_btn.pack(pady=(10, 20))

        # Load and display comments
        self._load_comments()
        self._display_comments(parent)

        # Comment section
        self._add_comment_section(parent)

    def _display_material(self, parent):
        """Display expanded material"""
        # Title
        title_text = self.item_data.get('title', 'Material')
        mat_type = self.item_data.get('material_type', 'Document')

        tk.Label(
            parent,
            text=f"📎 {title_text}",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#222222"
        ).pack(anchor=W, pady=(0, 10))

        # Description if any
        description = self.item_data.get('description', '')
        if description:
            tk.Label(
                parent,
                text=description,
                font=("Arial", 12),
                fg="white",
                bg="#222222",
                wraplength=800,
                justify=LEFT
            ).pack(anchor=W, pady=(0, 10))

        # Open/Download buttons (existing functionality)
        buttons_frame = tk.Frame(parent, bg="#222222")
        buttons_frame.pack(pady=(10, 20))

        file_path = self.item_data.get('file_path', '')
        if file_path:
            def open_material():
                import os
                if os.path.exists(file_path):
                    try:
                        # Use os.startfile for Windows
                        os.startfile(file_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not open file: {str(e)}")
                else:
                    messagebox.showerror("Error", "File not found")

            def download_material():
                import os
                import shutil
                from tkinter import filedialog
                if os.path.exists(file_path):
                    try:
                        # Get file extension
                        _, ext = os.path.splitext(file_path)
                        # Ask user where to save
                        save_path = filedialog.asksaveasfilename(
                            defaultextension=ext,
                            initialfile=f"{title_text}{ext}",
                            filetypes=[("All Files", "*.*")]
                        )
                        if save_path:
                            shutil.copy2(file_path, save_path)
                            messagebox.showinfo("Success", f"File downloaded to:\n{save_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not download file: {str(e)}")
                else:
                    messagebox.showerror("Error", "File not found")

            ttk.Button(
                buttons_frame,
                text="👁️ Open",
                command=open_material,
                bootstyle="primary"
            ).pack(side=LEFT, padx=(0, 10))

            ttk.Button(
                buttons_frame,
                text="⬇️ Download",
                command=download_material,
                bootstyle="info"
            ).pack(side=LEFT)
        else:
            # No file path, show disabled buttons or message
            tk.Label(
                buttons_frame,
                text="File not available",
                fg="white",
                bg="#222222"
            ).pack()

        # Load and display comments
        self._load_comments()
        self._display_comments(parent)

        # Comment section
        self._add_comment_section(parent)

    def _add_comment_section(self, parent):
        """Add comment button and text box"""
        comment_frame = tk.Frame(parent, bg="#222222")
        comment_frame.pack(fill=X, pady=(20, 0))

        self.comment_button = ttk.Button(
            comment_frame,
            text="💬 Comment",
            command=self._toggle_comment,
            bootstyle="outline-secondary"
        )
        self.comment_button.pack(anchor=W)

        # Comment input frame (initially hidden)
        self.comment_input_frame = tk.Frame(comment_frame, bg="#222222")
        # Don't pack it yet

        self.comment_text = tk.Text(
            self.comment_input_frame,
            height=4,
            width=80,
            wrap=tk.WORD,
            bg="#333333",
            fg="white",
            insertbackground="white"
        )
        self.comment_text.pack(side=LEFT, pady=(10, 0))

        # Send button
        self.send_button = ttk.Button(
            self.comment_input_frame,
            text="📤 Send",
            command=self._send_comment,
            bootstyle="success"
        )
        self.send_button.pack(side=LEFT, padx=(10, 0), pady=(10, 0))

    def _display_comments(self, parent):
        """Display existing comments with scroll bar"""
        # Comments section title
        tk.Label(
            parent,
            text="Comments",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#222222"
        ).pack(anchor=W, pady=(20, 10))

        # Scrollable comments area
        comments_frame = tk.Frame(parent, bg="#222222")
        comments_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        # Canvas and scrollbar
        canvas = tk.Canvas(comments_frame, bg="#222222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(comments_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#222222")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Display each comment
        for comment in self.comments:
            self._display_single_comment(scrollable_frame, comment)

        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Store references for updating
        self.comments_canvas = canvas
        self.comments_scrollable_frame = scrollable_frame

    def _display_single_comment(self, parent, comment):
        """Display a single comment"""
        comment_frame = tk.Frame(parent, bg="#333333", relief=SOLID, borderwidth=1)
        comment_frame.pack(fill=X, pady=5, padx=5)

        # Commenter name and timestamp
        header_frame = tk.Frame(comment_frame, bg="#333333")
        header_frame.pack(fill=X, padx=10, pady=5)

        commenter_name = comment.get('commenter_name', 'Unknown')
        tk.Label(
            header_frame,
            text=commenter_name,
            font=("Arial", 11, "bold"),
            fg="#cccccc",
            bg="#333333"
        ).pack(side=LEFT)

        timestamp = comment.get('timestamp', '')
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%b %d, %Y %I:%M %p')
            except:
                formatted_time = timestamp
        else:
            formatted_time = 'Unknown time'

        tk.Label(
            header_frame,
            text=formatted_time,
            font=("Arial", 9),
            fg="#888888",
            bg="#333333"
        ).pack(side=RIGHT)

        # Comment text
        comment_text = comment.get('comment_text', '')
        tk.Label(
            comment_frame,
            text=comment_text,
            font=("Arial", 10),
            fg="white",
            bg="#333333",
            wraplength=700,
            justify=LEFT,
            anchor="w"
        ).pack(anchor=W, padx=10, pady=(0, 10))

    def _update_comments_display(self):
        """Update the comments display when new comments are loaded"""
        print(f"[DEBUG EXPAND] _update_comments_display called with {len(self.comments)} comments")
        if hasattr(self, 'comments_scrollable_frame'):
            print(f"[DEBUG EXPAND] Clearing existing comment widgets")
            # Clear existing comments
            for widget in self.comments_scrollable_frame.winfo_children():
                widget.destroy()

            print(f"[DEBUG EXPAND] Displaying {len(self.comments)} updated comments")
            # Display updated comments
            for comment in self.comments:
                self._display_single_comment(self.comments_scrollable_frame, comment)

            # Update scroll region
            if hasattr(self, 'comments_canvas'):
                self.comments_canvas.configure(scrollregion=self.comments_canvas.bbox("all"))
                print(f"[DEBUG EXPAND] Updated scroll region")
        else:
            print(f"[DEBUG EXPAND] No comments_scrollable_frame to update")

    def _add_comment_section(self, parent):
        """Add comment button and text box"""
        comment_frame = tk.Frame(parent, bg="#222222")
        comment_frame.pack(fill=X, pady=(20, 0))

        self.comment_button = ttk.Button(
            comment_frame,
            text="💬 Comment",
            command=self._toggle_comment,
            bootstyle="outline-secondary"
        )
        self.comment_button.pack(anchor=W)

        # Comment input frame (initially hidden)
        self.comment_input_frame = tk.Frame(comment_frame, bg="#222222")
        # Don't pack it yet

        self.comment_text = tk.Text(
            self.comment_input_frame,
            height=4,
            width=80,
            wrap=tk.WORD,
            bg="#333333",
            fg="white",
            insertbackground="white"
        )
        self.comment_text.pack(side=LEFT, pady=(10, 0))

        # Send button
        self.send_button = ttk.Button(
            self.comment_input_frame,
            text="📤 Send",
            command=self._send_comment,
            bootstyle="success"
        )
        self.send_button.pack(side=LEFT, padx=(10, 0), pady=(10, 0))

    def _toggle_comment(self):
        """Toggle comment text box visibility"""
        if self.comment_visible:
            self.comment_input_frame.pack_forget()
            self.comment_button.config(text="💬 Comment")
            self.comment_visible = False
        else:
            self.comment_input_frame.pack(pady=(10, 0))
            self.comment_button.config(text="💬 Hide Comment")
            self.comment_visible = True

    def _send_comment(self):
        """Send the comment"""
        comment = self.comment_text.get("1.0", "end-1c").strip()
        if comment:
            # Get class_id from item_data or dashboard
            class_id = self.item_data.get('class_id') or self.dashboard.selected_class.get('_id')
            
            # Send comment
            result = self.dashboard.client.post_comment(
                self.item_data.get('_id'),
                self.item_type,
                class_id,
                comment
            )
            if result:
                messagebox.showinfo("Comment Sent", "Your comment has been sent successfully!")
                # Clear the text box
                self.comment_text.delete("1.0", "end")
                # Optionally refresh comments
                self._load_comments()
            else:
                messagebox.showerror("Error", "Failed to send comment.")
        else:
            messagebox.showwarning("Empty Comment", "Please enter a comment before sending.")

    def _back_to_main(self):
        """Go back to main view"""
        self.expanded_frame.destroy()
        self.dashboard.content_frame.pack(side=TOP, fill=BOTH, expand=YES)