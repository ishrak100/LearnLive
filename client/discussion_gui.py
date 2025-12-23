import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import os
import sys
import tkinter as tk

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.utility import LearnLiveClient


class DiscussionView:
    """Discussion page with chatbox-like interface for messaging"""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.messages = []  
        self.attached_file = None  

    def show(self):
        """Show the discussion view as full page"""

        # Hide main content frame
        self.dashboard.content_frame.pack_forget()
        self.dashboard.content_frame.update_idletasks()

        # Correct parent
        parent = self.dashboard.content_frame.master

        self._create_discussion_ui(parent)

    def create_tab_content(self, parent):
        """Create discussion UI inside a tab"""
        self._create_discussion_ui(parent)

    def _create_discussion_ui(self, parent):
        """Create the discussion UI elements"""
        # Discussion container
        self.discussion_frame = tk.Frame(parent, bg="#222222")
        self.discussion_frame.pack(fill=BOTH, expand=YES)

        # Back button area (only for full page)
        if hasattr(self.dashboard, 'content_frame') and parent == self.dashboard.content_frame.master:
            back_frame = tk.Frame(self.discussion_frame, bg="#222222")
            back_frame.pack(fill=X, padx=20, pady=10)

            ttk.Button(
                back_frame,
                text="← Back",
                command=self._back_to_main,
                bootstyle="secondary"
            ).pack(side=LEFT)

            # Title
            title_label = ttk.Label(
                back_frame,
                text="Discussion",
                font=("Helvetica", 16, "bold"),
                bootstyle="inverse-dark"
            )
            title_label.pack(side=LEFT, padx=(20, 0))

        # Main discussion area
        main_frame = ttk.Frame(self.discussion_frame, bootstyle="dark")
        main_frame.pack(fill=BOTH, expand=YES, padx=20, pady=10)

        # Chat display area (scrollable)
        chat_frame = ttk.Frame(main_frame, bootstyle="dark")
        chat_frame.pack(fill=BOTH, expand=YES)

        # Canvas and scrollbar for chat
        self.chat_canvas = tk.Canvas(chat_frame, bg="#222222", highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Frame inside canvas for messages
        self.messages_frame = tk.Frame(self.chat_canvas, bg="#222222")
        self.chat_canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        # Bind canvas resize
        self.messages_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))

        # Input area at bottom
        input_frame = ttk.Frame(main_frame, bootstyle="dark")
        input_frame.pack(fill=X, pady=(10, 0))

        # Attachment button
        self.attach_button = ttk.Button(
            input_frame,
            text="📎",
            command=self._attach_file,
            bootstyle="secondary",
            width=3
        )
        self.attach_button.pack(side=LEFT, padx=(0, 5))

        # Attachment label (shows selected file)
        self.attachment_label = ttk.Label(
            input_frame,
            text="",
            bootstyle="info",
            font=("Helvetica", 8)
        )
        self.attachment_label.pack(side=LEFT, padx=(0, 5))

        # Text input
        self.text_input = tk.Text(
            input_frame,
            height=3,
            bg="#3a3a3a",
            fg="white",
            insertbackground="white",
            font=("Helvetica", 10)
        )
        self.text_input.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))

        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="📤",
            command=self._send_message,
            bootstyle="primary",
            width=3
        )
        self.send_button.pack(side=LEFT)

        # Placeholder messages
        self._add_message("Welcome to the discussion!", "System")

    def _back_to_main(self):
        """Go back to main dashboard"""
        self.discussion_frame.pack_forget()
        self.dashboard.show_main_content()

    def _send_message(self):
        """Send a message with optional attachment"""
        message = self.text_input.get("1.0", tk.END).strip()
        
        if not message and not self.attached_file:
            messagebox.showwarning("Warning", "Please enter a message or attach a file.")
            return
        
        # Build message with attachment info if present
        if self.attached_file:
            file_name = self.attached_file['name']
            file_path = self.attached_file['path']
            if message:
                display_text = f"{message}\n📎 Attachment: {file_name}"
            else:
                display_text = f"📎 Attachment: {file_name}"
            self._add_message(display_text, "You")
            self.attached_file = None
            self.attachment_label.config(text="")
        else:
            self._add_message(message, "You")
        
        self.text_input.delete("1.0", tk.END)

    def _attach_file(self):
        """Attach a file to send with the message"""
        file_path = filedialog.askopenfilename(
            title="Select a file to attach",
            filetypes=[("All files", "*.*")]
        )
        if file_path:
            file_name = os.path.basename(file_path)
            self.attached_file = {'name': file_name, 'path': file_path}
            self.attachment_label.config(text=f"📎 {file_name}")
            messagebox.showinfo("File Selected", f"File '{file_name}' selected.\nType a caption and click send.")

    def _add_message(self, text, sender):
        """Add a message to the chat"""
        msg_frame = tk.Frame(self.messages_frame, bg="#222222")
        msg_frame.pack(fill=X, pady=2)

        sender_label = ttk.Label(
            msg_frame,
            text=f"{sender}:",
            font=("Helvetica", 9, "bold"),
            bootstyle="inverse-dark"
        )
        sender_label.pack(anchor="w")

        text_label = ttk.Label(
            msg_frame,
            text=text,
            wraplength=400,
            justify="left",
            bootstyle="inverse-dark"
        )
        text_label.pack(anchor="w", padx=(10, 0))

        # Update scroll region
        self.messages_frame.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)  # Scroll to bottom