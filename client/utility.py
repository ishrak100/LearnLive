import socket
import json
import threading
from typing import Callable, Optional
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE

class LearnLiveClient:
    """
    TCP Client for LearnLive classroom management system.
    Handles connection, message sending/receiving, and file transfers.
    """
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.token = None
        self.user_data = {}
        self.receive_thread = None
        self.running = False
        self.message_callback = None
        
    def connect(self, host: str = '127.0.0.1', port: int = SERVER_PORT) -> dict:
        """
        Connect to the LearnLive server.
        
        Args:
            host: Server hostname or IP
            port: Server port
            
        Returns:
            dict: Connection status
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.running = True
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            return {"success": True, "message": "Connected to server"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def disconnect(self):
        """Disconnect from the server."""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def set_message_callback(self, callback: Callable):
        """
        Set callback function for receiving messages.
        
        Args:
            callback: Function to call when message received
        """
        self.message_callback = callback
    
    def _receive_messages(self):
        """Background thread for receiving messages from server."""
        while self.running and self.connected:
            try:
                # Receive message length (4 bytes)
                length_data = b''
                while len(length_data) < 4:
                    chunk = self.socket.recv(4 - len(length_data))
                    if not chunk:
                        # Server closed connection
                        self.connected = False
                        if self.message_callback:
                            self.message_callback({
                                "type": "DISCONNECTED",
                                "message": "Server closed connection"
                            })
                        return
                    length_data += chunk
                
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Receive the full message
                data = b''
                while len(data) < message_length:
                    chunk = self.socket.recv(min(BUFFER_SIZE, message_length - len(data)))
                    if not chunk:
                        # Server closed connection
                        self.connected = False
                        if self.message_callback:
                            self.message_callback({
                                "type": "DISCONNECTED",
                                "message": "Server closed connection"
                            })
                        return
                    data += chunk
                
                # Parse the complete JSON message
                try:
                    message = json.loads(data.decode())
                    
                    # DEBUG: Print received message
                    print(f"📥 Client received: {message}")
                    
                    # Call callback if set
                    if self.message_callback:
                        self.message_callback(message)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    
            except Exception as e:
                if self.running:  # Only report if not intentional disconnect
                    # Don't show connection errors for expected disconnections
                    error_str = str(e).lower()
                    if 'bad' not in error_str and 'connection' in error_str:
                        if self.message_callback:
                            self.message_callback({
                                "type": "ERROR",
                                "error": f"Connection error: {str(e)}"
                            })
                break
    
    def send_message(self, message_type: str, data: dict = None) -> bool:
        """
        Send a message to the server.
        
        Args:
            message_type: Type of message (LOGIN, CREATE_CLASS, etc.)
            data: Message data
            
        Returns:
            bool: True if sent successfully
        """
        if not self.connected:
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data or {}
            }
            
            # Add token if authenticated
            if self.token:
                message["token"] = self.token
            
            # Send JSON message with length prefix
            json_data = json.dumps(message).encode()
            message_length = len(json_data)
            length_prefix = message_length.to_bytes(4, byteorder='big')
            self.socket.sendall(length_prefix + json_data)
            
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def login(self, email: str, password: str) -> dict:
        """
        Login to the server.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            dict: Login response (will be received via callback)
        """
        return self.send_message("LOGIN", {
            "email": email,
            "password": password
        })
    
    def signup(self, name: str, email: str, password: str, role: str) -> bool:
        """
        Create a new account.
        
        Args:
            name: User full name
            email: User email
            password: User password
            role: User role (teacher or student)
            
        Returns:
            bool: True if request sent
        """
        return self.send_message("SIGNUP", {
            "name": name,
            "email": email,
            "password": password,
            "role": role
        })
    
    def create_class(self, name: str = None, section: str = None, subject: str = None, room: str = None, class_name: str = None, description: str = None) -> bool:
        """Create a new class (teacher only)."""
        # Support both old and new parameter names
        if class_name is None:
            class_name = name
        if description is None:
            description = section or ""
            
        return self.send_message("CREATE_CLASS", {
            "class_name": class_name,
            "section": section or "",
            "subject": subject or "",
            "room": room or "",
            "description": description
        })
    
    def join_class(self, class_code: str) -> bool:
        """Join a class using class code (student only)."""
        return self.send_message("JOIN_CLASS", {
            "class_code": class_code
        })
    
    def view_classes(self) -> bool:
        """Get user's classes."""
        return self.send_message("VIEW_CLASSES")
    
    def view_students(self, class_id: str) -> bool:
        """View students in a class."""
        return self.send_message("VIEW_STUDENTS", {
            "class_id": class_id
        })
    
    def remove_student(self, class_id: str, student_id: str) -> bool:
        """Remove a student from class (teacher only)."""
        return self.send_message("REMOVE_STUDENT", {
            "class_id": class_id,
            "student_id": student_id
        })
    
    def delete_class(self, class_id: str) -> bool:
        """Delete a class (teacher only)."""
        return self.send_message("DELETE_CLASS", {
            "class_id": class_id
        })
    
    def create_assignment(self, class_id: str, title: str, description: str, 
                         due_date: str, max_points: int) -> bool:
        """Create an assignment (teacher only)."""
        return self.send_message("CREATE_ASSIGNMENT", {
            "class_id": class_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "max_points": max_points
        })
    
    def view_assignments(self, class_id: str) -> bool:
        """View assignments for a class."""
        return self.send_message("VIEW_ASSIGNMENTS", {
            "class_id": class_id
        })
    
    def submit_assignment(self, assignment_id: str, submission_text: str, 
                         file_path: str = None) -> bool:
        """Submit an assignment (student only)."""
        data = {
            "assignment_id": assignment_id,
            "submission_text": submission_text
        }
        
        if file_path:
            data["file_path"] = file_path
        
        return self.send_message("SUBMIT_ASSIGNMENT", data)
    
    def view_submissions(self, assignment_id: str) -> bool:
        """View submissions for an assignment (teacher only)."""
        return self.send_message("VIEW_SUBMISSIONS", {
            "assignment_id": assignment_id
        })
    
    def get_student_submission(self, assignment_id: str, student_id: str) -> bool:
        """Get a specific student's submission for an assignment."""
        print(f"[DEBUG CLIENT] get_student_submission called with assignment_id={assignment_id}, student_id={student_id}")
        result = self.send_message("GET_STUDENT_SUBMISSION", {
            "assignment_id": assignment_id,
            "student_id": student_id
        })
        print(f"[DEBUG CLIENT] send_message returned: {result}")
        return result
    
    def post_announcement(self, class_id: str, title: str, content: str) -> bool:
        """Post an announcement (teacher only)."""
        return self.send_message("POST_ANNOUNCEMENT", {
            "class_id": class_id,
            "title": title,
            "content": content
        })
    
    def view_announcements(self, class_id: str) -> bool:
        """View announcements for a class."""
        return self.send_message("VIEW_ANNOUNCEMENTS", {
            "class_id": class_id
        })
    
    def post_comment(self, announcement_id: str, comment_text: str) -> bool:
        """Post a comment on announcement."""
        return self.send_message("POST_COMMENT", {
            "announcement_id": announcement_id,
            "comment_text": comment_text
        })
    
    def view_comments(self, announcement_id: str) -> bool:
        """View comments on announcement."""
        return self.send_message("VIEW_COMMENTS", {
            "announcement_id": announcement_id
        })
    
    def upload_material(self, class_id: str, material_name: str, 
                       material_type: str, file_path: str) -> bool:
        """Upload class material (teacher only)."""
        return self.send_message("UPLOAD_MATERIAL", {
            "class_id": class_id,
            "title": material_name,
            "material_type": material_type,
            "file_path": file_path
        })
    
    def view_materials(self, class_id: str) -> bool:
        """View materials for a class."""
        return self.send_message("VIEW_MATERIALS", {
            "class_id": class_id
        })
    
    def upload_file(self, file_path: str, metadata: dict = None) -> bool:
        """
        Upload a file to the server using chunked transfer.
        
        Args:
            file_path: Path to file to upload
            metadata: Optional file metadata
            
        Returns:
            bool: True if upload started
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # Send start transfer message
            start_data = {
                "file_name": file_name,
                "file_size": file_size,
                "metadata": metadata or {}
            }
            
            if not self.send_message("START_FILE_TRANSFER", start_data):
                return False
            
            # TODO: Wait for server ACK, then send chunks
            # This will be implemented with proper async handling in GUI
            
            return True
            
        except Exception as e:
            print(f"Upload error: {e}")
            return False
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """
        Download a file from the server.
        
        Args:
            file_id: ID of file to download
            save_path: Path to save file
            
        Returns:
            bool: True if download started
        """
        return self.send_message("DOWNLOAD_FILE", {
            "file_id": file_id,
            "save_path": save_path
        })
    
    def get_notifications(self, user_id: str) -> bool:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if request sent
        """
        return self.send_message("GET_NOTIFICATIONS", {
            "user_id": user_id
        })
