import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

class DiscussionGUI:
    def __init__(self, parent, client, class_id, class_name, user_email, message_callback):
        """
        Initialize Discussion GUI
    
        Args:
            parent: Parent widget
            client: LearnLiveClient instance
            class_id: Class ID for discussion
            class_name: Class name for display
            user_email: Current user's email
            message_callback: Callback function to handle server responses
        """
        self.parent = parent
        self.client = client
        self.class_id = class_id
        self.class_name = class_name
        self.user_email = user_email
        self.message_callback = message_callback
    
        # Store pending messages locally
        self.pending_messages = {}  # local_id -> message_data
        self.local_message_counter = 0
        self.messages_cache = []  # Cache for server messages
    
        # GUI setup
        self._setup_ui()
    
        # Load initial messages once
        self.load_messages()
    
        # Register this GUI to receive server messages
        self._register_message_handlers()
    
    def _setup_ui(self):
        """Setup the discussion UI"""
        # Main container
        self.main_frame = ttk.Frame(self.parent, bootstyle="dark")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text=f"💬 Discussion - {self.class_name}",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-light"
        ).pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(
            header_frame,
            text="🔄 Refresh",
            bootstyle="info-outline",
            command=self.load_messages,
            width=10
        ).pack(side=tk.RIGHT)
        
        # Messages display area with scrollbar
        messages_container = ttk.Frame(self.main_frame)
        messages_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a Canvas with scrollbar for better performance
        self.canvas = tk.Canvas(
            messages_container,
            bg="#2b2b2b",
            highlightthickness=0
        )
        
        scrollbar = ttk.Scrollbar(
            messages_container, 
            orient=tk.VERTICAL, 
            command=self.canvas.yview
        )
        
        self.messages_frame = ttk.Frame(self.canvas)
        self.messages_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Message input area
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X)
        
        # Message input with scrollbar
        input_container = ttk.Frame(input_frame)
        input_container.pack(fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.message_input = tk.Text(
            input_container,
            height=3,
            wrap=tk.WORD,
            font=("Arial", 11)
        )
        
        input_scrollbar = ttk.Scrollbar(
            input_container, 
            command=self.message_input.yview
        )
        self.message_input.configure(yscrollcommand=input_scrollbar.set)
        
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            bootstyle="success",
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Bind Enter key (Ctrl+Enter or Cmd+Enter to send)
        self.message_input.bind("<Control-Return>", lambda e: self.send_message())
        self.message_input.bind("<Command-Return>", lambda e: self.send_message())
        self.message_input.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for new line
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready",
            font=("Arial", 9),
            bootstyle="light"
        )
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _register_message_handlers(self):
        """Register handlers for server message responses"""
        pass
    
    def handle_server_message(self, response):
        """
        Handle messages received from server
        
        This should be called from the main application's message callback
        """
        msg_type = response.get('type', '')
        print(f"[DEBUG GUI] handle_server_message: type={msg_type}")
        
        if msg_type == 'SUCCESS':
            if 'messages' in response:
                # This is a response to fetch_messages
                print(f"[DEBUG GUI] Got messages response: {len(response['messages'])} messages")
                self.messages_cache = response['messages']
                self.display_messages(response['messages'])
                self.status_label.config(text=f"Loaded {len(response['messages'])} messages")
                
            elif 'message' in response:
                # This is a response to post_message
                server_msg = response['message']
                print(f"[DEBUG GUI] Message sent to server: {server_msg}")
                
                # Update any pending local message with server data
                for local_id, local_msg in list(self.pending_messages.items()):
                    if (local_msg['content'] == server_msg.get('content') and 
                        local_msg['sent_by'] == server_msg.get('sent_by')):
                        # Remove from pending
                        del self.pending_messages[local_id]
                        # Refresh to get server version
                        self.load_messages()
                        break
                
                self.status_label.config(text="Message sent successfully")
    
        elif msg_type == 'MESSAGE':
            # Real-time broadcast message
            print(f"[DEBUG GUI] Real-time message received!")
            message_data = response.get('message', {})
            self.add_new_message(message_data)
            
        elif msg_type == 'ERROR':
            error_msg = response.get('error', 'Unknown error')
            self.status_label.config(text=f"Error: {error_msg}")
            print(f"[DEBUG GUI] Error: {error_msg}")
            
            # If it's a message sending error, mark pending message as failed
            if 'message' in response.get('data', {}):
                for local_id, local_msg in self.pending_messages.items():
                    if local_msg.get('status') == 'sending':
                        local_msg['status'] = 'failed'
                        self.update_message_display()
                        break
    
    def send_message(self):
        """Send message without blocking UI"""
        content = self.message_input.get("1.0", tk.END).strip()
        if not content:
            return
        
        print(f"[DEBUG GUI] Sending message: '{content}'")
        
        # Clear input immediately
        self.message_input.delete("1.0", tk.END)
        
        # Disable send button temporarily
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(text="Sending message...")
        
        # Create local message for instant display
        local_id = f"local_{self.local_message_counter}"
        self.local_message_counter += 1
        
        local_message = {
            'msg_id': local_id,
            'content': content,
            'class_id': self.class_id,
            'sent_by': self.user_email,
            'created_at': datetime.now().isoformat(),
            'status': 'sending',
            'is_local': True
        }
        
        # Store locally
        self.pending_messages[local_id] = local_message
        
        # Display message locally immediately
        self.display_message(local_message)
        
        # Send in background thread
        threading.Thread(
            target=self._send_message_thread,
            args=(content,),
            daemon=True
        ).start()
    
    def _send_message_thread(self, content):
        """Background thread to send message to server"""
        try:
            print(f"[DEBUG GUI] Thread started for sending message")
            
            # Send via client
            success = self.client.post_message(content, self.class_id)
            
            print(f"[DEBUG GUI] Client.post_message returned: {success}")
            
            # Re-enable send button regardless of success/failure
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            
            if success:
                print(f"[DEBUG GUI] Message sent successfully")
                self.status_label.config(text="Message sent successfully")
                # Refresh to get server-stored version
                self.load_messages()
            else:
                print(f"[DEBUG GUI] Failed to send message")
                self.status_label.config(text="Failed to send message")
                
        except Exception as e:
            print(f"[DEBUG GUI] Error: {str(e)}")
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            self.status_label.config(text=f"Error: {str(e)}")
    
    def load_messages(self):
        """Load messages from server in background thread"""
        def load_thread():
            print(f"[DEBUG GUI] Loading messages for class: {self.class_id}")
            self.status_label.config(text="Loading messages...")
            try:
                # This sends FETCH_MESSAGES request
                success = self.client.fetch_messages(self.class_id, 50)
                print(f"[DEBUG GUI] fetch_messages called, result: {success}")
            except Exception as e:
                print(f"[DEBUG GUI] Error loading messages: {str(e)}")
                if self.parent and self.parent.winfo_exists():
                    self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
        
        # Run in thread to avoid blocking
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
    
    def add_new_message(self, message_data):
        """Add a new message to the display (for real-time updates)"""
        print(f"[DEBUG GUI] Adding new message: {message_data}")
        
        # Check if message is already in cache
        msg_id = message_data.get('msg_id') or message_data.get('_id')
        for msg in self.messages_cache:
            if (msg.get('msg_id') == msg_id or msg.get('_id') == msg_id):
                print(f"[DEBUG GUI] Message already in cache, skipping")
                return
        
        # Add message to cache
        self.messages_cache.append(message_data)
        
        # If the message is not from current user, display it immediately
        if message_data.get('sent_by') != self.user_email:
            print(f"[DEBUG GUI] Displaying message from others immediately")
            self.display_message(message_data)
            if self.canvas and self.canvas.winfo_exists():
                self.canvas.yview_moveto(1.0)  # Scroll to bottom
        
        # Also refresh the full list to ensure consistency
        self.load_messages()
    
    def display_message(self, message):
        """Display a single message in the messages frame"""
        # Create message frame
        msg_frame = ttk.Frame(self.messages_frame)
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Configure colors based on sender
        is_me = message.get('sent_by') == self.user_email
        bg_color = "#1e3a1e" if is_me else "#1e1e3a"  # Green for me, blue for others
        fg_color = "#4CAF50" if is_me else "#2196F3"
        
        # Message container
        container = tk.Frame(
            msg_frame,
            bg=bg_color,
            relief=tk.RAISED,
            bd=1
        )
        container.pack(
            fill=tk.X, 
            side=tk.RIGHT if is_me else tk.LEFT,
            expand=True
        )
        
        # Sender label
        sender_text = "You" if is_me else message.get('sent_by', 'Unknown')
        sender_label = tk.Label(
            container,
            text=f"{sender_text}:",
            bg=bg_color,
            fg=fg_color,
            font=("Arial", 11, "bold"),
            anchor="w"
        )
        sender_label.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Content label
        content_label = tk.Label(
            container,
            text=message.get('content', ''),
            bg=bg_color,
            fg="white",
            font=("Arial", 11),
            wraplength=400,
            justify=tk.LEFT,
            anchor="w"
        )
        content_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Timestamp and status
        timestamp = message.get('created_at', '')
        if timestamp:
            try:
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime("%I:%M %p")
                else:
                    timestamp_str = timestamp
            except:
                timestamp_str = timestamp
        else:
            timestamp_str = ""
        
        status = message.get('status', '')
        if status == 'sending':
            status_text = "⏳ Sending..."
            status_color = "#FF9800"
        elif status == 'failed':
            status_text = "❌ Failed"
            status_color = "#F44336"
        else:
            status_text = timestamp_str
            status_color = "#888888"
        
        status_frame = tk.Frame(container, bg=bg_color)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        status_label = tk.Label(
            status_frame,
            text=status_text,
            bg=bg_color,
            fg=status_color,
            font=("Arial", 9)
        )
        status_label.pack(side=tk.RIGHT)
    
    def display_messages(self, messages):
        """Display all messages (clear and redraw)"""
        # Clear existing messages
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        # Combine server messages with pending local messages
        all_messages = []
        
        # Add server messages
        for msg in messages:
            msg['is_local'] = False
            all_messages.append(msg)
        
        # Add pending local messages
        for local_msg in self.pending_messages.values():
            # Only add if not already in server messages
            if local_msg['status'] != 'sent':
                all_messages.append(local_msg)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get('created_at', ''))
        
        # Display all messages
        for msg in all_messages:
            self.display_message(msg)
        
        # Scroll to bottom
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.yview_moveto(1.0)
    
    def update_message_display(self):
        """Update the display with current messages"""
        self.load_messages()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.main_frame and self.main_frame.winfo_exists():
                self.main_frame.destroy()
        except:
            pass