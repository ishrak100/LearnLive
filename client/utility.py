import socket
import json
import threading
import uuid
import time
from typing import Callable, Optional
import os
import sys

# Add parent directory to path
MSG_POST_MESSAGE = "POST_MESSAGE"
MSG_FETCH_MESSAGES = "FETCH_MESSAGES"
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
        self.server_address = (SERVER_HOST, SERVER_PORT)
        self.pending_download = None  # NEW: Track pending download
        
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
                    
                    # NEW: Check if this is a file download response
                    if (message.get('type') == 'SUCCESS' and 
                        'size' in message and 
                        'filename' in message and
                        self.pending_download is not None):
                        
                        print(f"[CLIENT] File metadata received, expecting {message['size']} bytes")
                        
                        # Now read binary data directly from socket
                        size = message.get('size', 0)
                        if size > 0:
                            binary_data = b""
                            bytes_received = 0
                            
                            while bytes_received < size:
                                remaining = size - bytes_received
                                chunk = self.socket.recv(min(4096, remaining))
                                if not chunk:
                                    break
                                binary_data += chunk
                                bytes_received += len(chunk)
                            
                            print(f"[CLIENT] Received {len(binary_data)} bytes of binary data")
                            
                            # Create complete download response
                            download_response = {
                                "type": "FILE_DOWNLOAD_COMPLETE",
                                "success": True,
                                "filename": message.get('filename'),
                                "binary_data": binary_data,
                                "size": len(binary_data),
                                "content_type": message.get('content_type'),
                                "request_id": self.pending_download
                            }
                            
                            # Reset pending download
                            self.pending_download = None
                            
                            # Call callback with complete file
                            if self.message_callback:
                                self.message_callback(download_response)
                            
                            # Skip normal callback for metadata
                            continue
                    
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
    
    def submit_assignment_gridfs(self, assignment_id, user_id, file_content, filename=None):
        """Submit assignment with GridFS storage using binary protocol (identical to material upload)"""
    
        if filename is None:
            filename = "assignment_submission.bin"

        print(f"[CLIENT ASSIGNMENT] Submitting assignment: {assignment_id}, size: {len(file_content)} bytes")
    
        data_payload = {
            "assignment_id": assignment_id,
            "user_id": user_id,
            "filename": filename,
            "file_size": len(file_content),
            "user_role": "student"  # ← CRITICAL: Add user_role like material upload
        }

        send_success = self.send_message("SUBMIT_ASSIGNMENT_GRIDFS", data_payload)
        if not send_success:
           print("[CLIENT ASSIGNMENT ERROR] Failed to send metadata")
           return {'success': False, 'error': 'Failed to send metadata'}

        print(f"[CLIENT ASSIGNMENT] Metadata sent, sending {len(file_content)} bytes of binary data")
    
        try:
            self.socket.sendall(file_content)
            print("[CLIENT ASSIGNMENT] Binary data sent successfully")
            return {'success': True}  # ← Fire-and-forget, no waiting for response

        except Exception as e:
            print(f"[CLIENT ASSIGNMENT ERROR] Failed to send binary data: {e}")
            return {'success': False, 'error': f'Failed to send binary data: {str(e)}'}
    
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
    
    def post_comment(self, item_id: str, item_type: str, class_id: str, comment_text: str) -> bool:
        """Post a comment on an item (announcement, assignment, or material)."""
        return self.send_message("POST_COMMENT", {
            "item_id": item_id,
            "item_type": item_type,
            "class_id": class_id,
            "comment_text": comment_text
        })
    
    def view_comments(self, item_id: str, item_type: str) -> bool:
        """View comments on an item."""
        return self.send_message("VIEW_COMMENTS", {
            "item_id": item_id,
            "item_type": item_type
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
    
    # REMOVED duplicate get_notifications method
    
    # NEW: Fixed download_file_binary method
    def download_file_binary(self, file_id):
        """
        Download a file from the server using the SAME socket connection.
        The file will be delivered via the message callback as FILE_DOWNLOAD_COMPLETE.
        
        Returns:
            dict: Initial response with request_id
        """
        try:
            # Generate a unique request ID
            request_id = str(uuid.uuid4())[:8]
            
            # Store that we're expecting a download
            self.pending_download = request_id
            
            # Send the download request using the standard protocol
            success = self.send_message("DOWNLOAD_FILE", {
                "file_id": file_id,
                "request_id": request_id
            })
            
            if not success:
                self.pending_download = None
                return {
                    'success': False, 
                    'error': 'Failed to send download request'
                }
            
            print(f"[CLIENT] Download request sent for file_id: {file_id}, request_id: {request_id}")
            
            return {
                'success': True,
                'message': 'Download request sent',
                'request_id': request_id,
                'status': 'pending'
            }
            
        except Exception as e:
            print(f"[CLIENT DOWNLOAD ERROR] {e}")
            self.pending_download = None
            return {'success': False, 'error': str(e)}
     
        
    def upload_material_gridfs(self, class_id, teacher_id, title, material_type, file_content, filename=None):
        """Upload material with GridFS storage using binary protocol (NON-BLOCKING, assignment-style)"""

        if filename is None:
            filename = "material.bin"

        print(f"[CLIENT MATERIAL] Uploading material: {title}, size: {len(file_content)} bytes")
    
         
        data_payload = {
            "class_id": class_id,
            "teacher_id": teacher_id,
            "title": title,
            "material_type": material_type,
            "filename": filename,
            "file_size": len(file_content),
            "user_role": "teacher"
        }

        
        send_success = self.send_message("UPLOAD_MATERIAL_GRIDFS", data_payload)
        if not send_success:
            print("[CLIENT MATERIAL ERROR] Failed to send metadata")
            return {'success': False, 'error': 'Failed to send metadata'}

        print(f"[CLIENT MATERIAL] Metadata sent, sending {len(file_content)} bytes of binary data")

        
        try:
            self.socket.sendall(file_content)
            print("[CLIENT MATERIAL] Binary data sent successfully")


            return {'success': True}

        except Exception as e:
            print(f"[CLIENT MATERIAL ERROR] Failed to send binary data: {e}")
            return {'success': False, 'error': f'Failed to send binary data: {str(e)}'}
        
        # Add these methods after the existing methods like upload_material_gridfs:

    def post_message(self, content, class_id):
        """Send a discussion message - NON-BLOCKING VERSION"""
        print(f"[DEBUG CLIENT] post_message called: content={content}, class_id={class_id}")
    
        # Get user email from user_data
        sent_by = ""
        if hasattr(self, 'user_data') and self.user_data:
            sent_by = self.user_data.get('email', '')
        elif hasattr(self, 'email'):
            sent_by = self.email
        else:
            print(f"[DEBUG CLIENT] Warning: No user email found!")
            sent_by = "unknown"
    
        data = {
            "content": content,
            "class_id": class_id,
            "sent_by": sent_by,  # Use email instead of user_id
        }
    
        print(f"[DEBUG CLIENT] Sending POST_MESSAGE with data: {data}")
    
        # Use send_message (which is already non-blocking) instead of send_message_to_server
        result = self.send_message("POST_MESSAGE", data)
        print(f"[DEBUG CLIENT] send_message returned: {result}")
    
        return result
    
    def fetch_messages(self, class_id: str, limit: int = 100) -> bool:
        """Fetch discussion messages for a class."""
        return self.send_message("FETCH_MESSAGES", {
            "class_id": class_id,
            "limit": limit
        })
