# Main TCP Server for LearnLive

import socket
import threading
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import *
from server.database import Database
from server.file_handler import FileHandler
from server.notification import NotificationHandler
from server.discussion_handler import DiscussionHandler


class LearnLiveServer:
    def __init__(self):
        """Initialize the TCP server"""
        self.host = SERVER_HOST
        self.port = SERVER_PORT
        self.server_socket = None
        self.clients = {}  # token -> (socket, user_data)
        self.db = Database()
        self.file_handler = FileHandler()
        self.notifier = NotificationHandler(self.db)  # Pass database reference
        # Discussion handler: use its own DiscussionDB implementation
        # (passing the general Database instance caused missing `send_message` errors)
        self.discussion = DiscussionHandler()
        self.running = False
        
        print(f"🎓 LearnLive Server Initializing...")
        print(f"📡 Host: {self.host}")
        print(f"🔌 Port: {self.port}")
    
    def start(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CLIENTS)
            self.running = True
            
            print(f"\n✅ Server started successfully!")
            print(f"🌐 Listening on {self.host}:{self.port}")
            print(f"👥 Max clients: {MAX_CLIENTS}")
            print(f"📦 Buffer size: {BUFFER_SIZE} bytes")
            print(f"\n⏳ Waiting for connections...\n")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"\n========== NEW CONNECTION ==========")
                    print(f"✅ Client connected from {address[0]}:{address[1]}")
                    print(f"🔗 Protocol: TCP (Connection-oriented)")
                    print(f"====================================\n")
                    
                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Error accepting connection: {e}")
        
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        current_token = None
        current_user_id = None
        
        try:
            while self.running:
                # Receive message length (4 bytes)
                length_data = b''
                while len(length_data) < 4:
                    chunk = client_socket.recv(4 - len(length_data))
                    if not chunk:
                        print(f"🔌 Client {address} disconnected")
                        return
                    length_data += chunk
                
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Receive the full message
                data = b''
                while len(data) < message_length:
                    chunk = client_socket.recv(min(BUFFER_SIZE, message_length - len(data)))
                    if not chunk:
                        print(f"🔌 Client {address} disconnected")
                        return
                    data += chunk
                
                print(f"\n📨 TCP SEGMENT RECEIVED")
                print(f"   From: {address[0]}:{address[1]}")
                print(f"   Size: {len(data)} bytes")
                print(f"   Protocol: TCP (Reliable, Ordered)")
                
                # Parse message
                try:
                    message = json.loads(data.decode())
                    msg_type = message.get('type')
                    
                    print(f"   Message Type: {msg_type}")
                    
                    # Handle message based on type
                    response = self.process_message(message, client_socket, address)
                    
                    # DEBUG: Print response (excluding large file data)
                    response_summary = response.copy()
                    
                    # Suppress file_data in direct response
                    if 'file_data' in response_summary:
                        response_summary['file_data'] = f"<{len(response['file_data'])} bytes>"
                    
                    # Suppress file_data in submission object
                    if 'submission' in response_summary and isinstance(response_summary['submission'], dict):
                        if 'file_data' in response_summary['submission']:
                            response_summary['submission'] = response_summary['submission'].copy()
                            response_summary['submission']['file_data'] = f"<{len(response['submission']['file_data'])} bytes>"
                    
                    # Suppress file_data in submissions array
                    if 'submissions' in response_summary and isinstance(response_summary['submissions'], list):
                        cleaned_submissions = []
                        for sub in response_summary['submissions']:
                            if isinstance(sub, dict) and 'file_data' in sub:
                                cleaned_sub = sub.copy()
                                cleaned_sub['file_data'] = f"<{len(sub['file_data'])} bytes>"
                                cleaned_submissions.append(cleaned_sub)
                            else:
                                cleaned_submissions.append(sub)
                        response_summary['submissions'] = cleaned_submissions
                    
                    print(f"   📤 Response: {response_summary}")
                    
                    # Track token for cleanup
                    if msg_type in [MSG_LOGIN, MSG_SIGNUP] and response.get('success'):
                        current_token = response.get('token')
                        current_user_id = response.get('user_id')
                        self.clients[current_token] = (client_socket, response)
                        
                        # Register client with notification system
                        user_id = response.get('user_id')
                        user_data = {
                            'name': response.get('name'),
                            'email': response.get('email'),
                            'role': response.get('role')
                        }
                        self.notifier.register_client(user_id, client_socket, user_data)
                        print(f"📲 Client registered for notifications: {user_data.get('name')} ({user_id})")
                    
                    # Send response with length prefix
                    try:
                        response_data = json.dumps(response).encode()
                        message_length = len(response_data)
                        length_prefix = message_length.to_bytes(4, byteorder='big')
                        client_socket.sendall(length_prefix + response_data)
                        
                        print(f"   ✅ Response sent ({len(response_data)} bytes)\n")
                    except (TypeError, ValueError) as e:
                        # JSON serialization failed (e.g., datetime objects)
                        print(f"   ❌ JSON serialization error: {e}")
                        error_response = {
                            'type': RESP_ERROR,
                            'error': 'Server serialization error'
                        }
                        error_data = json.dumps(error_response).encode()
                        error_length = len(error_data)
                        length_prefix = error_length.to_bytes(4, byteorder='big')
                        client_socket.sendall(length_prefix + error_data)
                        print(f"   ❌ Error response sent\n")
                    
                except json.JSONDecodeError:
                    error_response = {
                        'type': RESP_ERROR,
                        'error': 'Invalid JSON format'
                    }
                    error_data = json.dumps(error_response).encode()
                    error_length = len(error_data)
                    length_prefix = error_length.to_bytes(4, byteorder='big')
                    client_socket.sendall(length_prefix + error_data)
                    error_response = {
                        'type': RESP_ERROR,
                        'error': 'Invalid JSON format'
                    }
                    error_data = json.dumps(error_response).encode()
                    error_length = len(error_data)
                    length_prefix = error_length.to_bytes(4, byteorder='big')
                    client_socket.sendall(length_prefix + error_data)
                
        except Exception as e:
            print(f"❌ Error handling client {address}: {e}")
        
        finally:
            # Cleanup
            if current_token and current_token in self.clients:
                del self.clients[current_token]
            if current_user_id:
                self.notifier.unregister_client(current_user_id)
                print(f"📲 Client unregistered from notifications: {current_user_id}")
            client_socket.close()
            print(f"👋 Connection closed with {address}\n")
    
    def process_message(self, message, client_socket, address):
        """Process incoming message and return response"""
        msg_type = message.get('type')
        token = message.get('token')
        data = message.get('data', {})
        
        # Authentication required messages
        auth_required = [
            MSG_CREATE_CLASS, MSG_JOIN_CLASS, MSG_VIEW_CLASSES,
            MSG_CREATE_ASSIGNMENT, MSG_VIEW_ASSIGNMENTS, MSG_SUBMIT_ASSIGNMENT,
            MSG_VIEW_SUBMISSIONS, MSG_GET_STUDENT_SUBMISSION, MSG_POST_ANNOUNCEMENT, MSG_VIEW_ANNOUNCEMENTS,
            MSG_POST_COMMENT, MSG_VIEW_COMMENTS, MSG_UPLOAD_FILE,
            MSG_DOWNLOAD_FILE, MSG_REMOVE_STUDENT, MSG_DELETE_CLASS,
            MSG_VIEW_STUDENTS, MSG_UPLOAD_MATERIAL, MSG_VIEW_MATERIALS,
            MSG_GET_TEACHER_SUBMISSIONS, MSG_GET_STUDENT_ALL_ASSIGNMENTS, MSG_START_FILE_TRANSFER, 
            MSG_FILE_CHUNK, MSG_END_FILE_TRANSFER, MSG_POST_MESSAGE, MSG_GET_MESSAGES, MSG_SUBMIT_ASSIGNMENT_GRIDFS
        ]
        
        # Verify token if required
        if msg_type in auth_required:
            user_data = self.db.verify_token(token)
            if not user_data['success']:
                return {'type': RESP_ERROR, 'error': 'Unauthorized'}
            data['user_id'] = user_data['user_id']
            data['user_role'] = user_data['role']
            data['user_email'] = user_data['email']
        
        # Route to appropriate handler
        if msg_type == MSG_LOGIN:
            return self.handle_login(data)
        
        elif msg_type == MSG_SIGNUP:
            return self.handle_signup(data)
        
        elif msg_type == MSG_CREATE_CLASS:
            return self.handle_create_class(data)
        
        elif msg_type == MSG_JOIN_CLASS:
            return self.handle_join_class(data)
        
        elif msg_type == MSG_VIEW_CLASSES:
            return self.handle_view_classes(data)
        
        elif msg_type == MSG_CREATE_ASSIGNMENT:
            return self.handle_create_assignment(data)
        
        elif msg_type == MSG_VIEW_ASSIGNMENTS:
            return self.handle_view_assignments(data)
        
        elif msg_type == MSG_SUBMIT_ASSIGNMENT:
            return self.handle_submit_assignment(data)
        
        elif msg_type == MSG_VIEW_SUBMISSIONS:
            return self.handle_view_submissions(data)
        
        elif msg_type == MSG_GET_STUDENT_SUBMISSION:
            return self.handle_get_student_submission(data)
        
        elif msg_type == MSG_POST_ANNOUNCEMENT:
            return self.handle_post_announcement(data)
        
        elif msg_type == MSG_VIEW_ANNOUNCEMENTS:
            return self.handle_view_announcements(data)
        
        elif msg_type == MSG_POST_COMMENT:
            return self.handle_post_comment(data)
        
        elif msg_type == MSG_VIEW_COMMENTS:
            return self.handle_view_comments(data)
        
        elif msg_type == MSG_START_FILE_TRANSFER:
            return self.file_handler.handle_file_upload_start(data, client_socket)
        
        elif msg_type == MSG_FILE_CHUNK:
            return self.file_handler.handle_file_chunk(data)
        
        elif msg_type == MSG_END_FILE_TRANSFER:
            return self.file_handler.handle_file_upload_complete(data)
        
        elif msg_type == MSG_DOWNLOAD_FILE:
            return self.handle_download_file(data, client_socket, address) 
        
        elif msg_type == MSG_REMOVE_STUDENT:
            return self.handle_remove_student(data)
        
        elif msg_type == MSG_DELETE_CLASS:
            return self.handle_delete_class(data)
        
        elif msg_type == MSG_VIEW_STUDENTS:
            return self.handle_view_students(data)
        
        elif msg_type == MSG_UPLOAD_MATERIAL:
            return self.handle_upload_material(data)
        
        elif msg_type == MSG_VIEW_MATERIALS:
            return self.handle_view_materials(data)
        
        elif msg_type == MSG_GET_TEACHER_SUBMISSIONS:
            return self.handle_get_teacher_submissions(data)
        
        elif msg_type == MSG_GET_STUDENT_ALL_ASSIGNMENTS:
            return self.handle_get_student_all_assignments(data)
        
        elif msg_type == MSG_GET_NOTIFICATIONS:
            return self.handle_get_notifications(data)
        elif msg_type == MSG_SUBMIT_ASSIGNMENT_GRIDFS:
          return self.handle_submit_assignment_gridfs(data, client_socket, address)
        
        elif msg_type == MSG_UPLOAD_MATERIAL_GRIDFS:  # NEW: Add this line
         return self.handle_upload_material_gridfs(data, client_socket, address)
        

        elif msg_type == MSG_POST_MESSAGE:
            try:
                return self.discussion.send_message_handler(data)
            except AttributeError as e:
                # Defensive: if the discussion handler was constructed with the
                # generic Database lacking `send_message`, recreate a fresh
                # DiscussionHandler that uses the dedicated DiscussionDB and retry.
                err = str(e)
                print(f"[WARN] Discussion handler AttributeError: {err} - recreating handler and retrying")
                try:
                    from server.discussion_handler import DiscussionHandler
                    self.discussion = DiscussionHandler()
                    return self.discussion.send_message_handler(data)
                except Exception as e2:
                    print(f"[ERROR] Failed to recover DiscussionHandler: {e2}")
                    return {'type': RESP_ERROR, 'error': str(e2)}

        elif msg_type == MSG_GET_MESSAGES:
            try:
                return self.discussion.fetch_messages_handler(data)
            except AttributeError as e:
                print(f"[WARN] Discussion handler AttributeError on fetch: {e} - recreating handler and retrying")
                try:
                    from server.discussion_handler import DiscussionHandler
                    self.discussion = DiscussionHandler()
                    return self.discussion.fetch_messages_handler(data)
                except Exception as e2:
                    print(f"[ERROR] Failed to recover DiscussionHandler for fetch: {e2}")
                    return {'type': RESP_ERROR, 'error': str(e2)}
        
        else:
            return {'type': RESP_ERROR, 'error': 'Unknown message type'}
    
    # ========== MESSAGE HANDLERS ==========
    
    def handle_login(self, data):
        """Handle login request"""
        email = data.get('email')
        password = data.get('password')
        
        result = self.db.authenticate_user(email, password)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'token': result['token'],
                'user_id': result['user_id'],
                'name': result['name'],
                'email': result['email'],
                'role': result['role']
            }
        else:
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': result['error']
            }
    
    def handle_signup(self, data):
        """Handle signup request"""
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role')
        
        result = self.db.create_user(email, password, name, role)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'message': 'User created successfully',
                'user_id': result.get('user_id')
            }
        else:
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': result['error']
            }
    
    def handle_create_class(self, data):
        """Handle create class request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can create classes'}
        
        class_name = data.get('class_name')
        section = data.get('section', '')
        subject = data.get('subject', '')
        room = data.get('room', '')
        description = data.get('description', '')
        
        result = self.db.create_class(data['user_id'], class_name, section, subject, room, description)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'message': f'Class created successfully! Class Code: {result["class_code"]}',
                'class_id': result['class_id'],
                'class_code': result['class_code']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_join_class(self, data):
        """Handle join class request"""
        if data['user_role'] != 'student':
            return {'type': RESP_ERROR, 'error': 'Only students can join classes'}
        
        class_code = data.get('class_code')
        result = self.db.join_class(data['user_id'], class_code)
        
        if result['success']:
            # Send notification to teacher
            self.notifier.notify_student_joined(class_code, data['user_email'])
            
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'class_id': result['class_id']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_view_classes(self, data):
        """Handle view classes request"""
        result = self.db.get_user_classes(data['user_id'], data['user_role'])
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'classes': result['classes']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_create_assignment(self, data):
        """Handle create assignment request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can create assignments'}
        
        class_id = data.get('class_id')
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        max_points = data.get('max_points', 100)
        
        result = self.db.create_assignment(class_id, title, description, due_date, max_points)
        
        if result['success']:
            # Get class data and student emails for notifications
            class_data = self.db.get_class_by_id(class_id)
            if class_data['success'] and class_data['class']:
                class_info = class_data['class']
                student_emails = []
                
                # Get student emails from enrolled_students
                for student_id in class_info.get('enrolled_students', []):
                    student = self.db.get_user_by_id(student_id)
                    if student['success']:
                        student_emails.append(student['user'].get('email'))
                
                # Send notifications (email + TCP)
                assignment_data = {
                    'title': title,
                    'description': description,
                    'due_date': due_date,
                    'created_at': result.get('created_at', '')
                }
                self.notifier.notify_assignment_created(class_info, assignment_data, student_emails)
            
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'assignment_id': result['assignment_id']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_view_assignments(self, data):
        """Handle view assignments request"""
        class_id = data.get('class_id')
        result = self.db.get_assignments(class_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'assignments': result['assignments']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_submit_assignment(self, data):
        """Handle submit assignment request"""
        if data['user_role'] != 'student':
            return {'type': RESP_ERROR, 'error': 'Only students can submit assignments'}

        assignment_id = data.get('assignment_id')
        file_data_hex = data.get('file_data')  # This is HEX encoded string from client
        text_content = data.get('text_content', '')
        filename = data.get('filename', '')  # Get original filename

        # Convert hex string back to binary
        file_content = None
        if file_data_hex:
            try:
                # Decode hex string to binary
                file_content = bytes.fromhex(file_data_hex)
            except Exception as e:
                return {
                    'type': RESP_ERROR, 
                    'success': False, 
                    'error': f'Invalid file data format: {str(e)}'
                }

        # Check if we have either file or text content
        if not file_content and not text_content:
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': 'Submission must contain either a file or text content'
            }

        try:
            result = self.db.submit_assignment(assignment_id, data['user_id'], file_content, text_content, filename)
 
            if result['success']:
                return {
                    'type': RESP_SUCCESS,
                    'success': True,
                    'submission_id': result['submission_id']
                }
            else:
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': result['error']
                }

        except Exception as e:
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': f'Server error: {str(e)}'
            }


    def handle_view_submissions(self, data):
        """Handle view submissions request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can view submissions'}
        
        assignment_id = data.get('assignment_id')
        result = self.db.get_submissions(assignment_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'submissions': result['submissions']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_get_student_submission(self, data):
        """Handle get student submission request"""
        assignment_id = data.get('assignment_id')
        student_id = data.get('student_id')
        
        print(f"[DEBUG SERVER] handle_get_student_submission called: assignment_id={assignment_id}, student_id={student_id}")
        
        result = self.db.get_student_submission(assignment_id, student_id)
        
        print(f"[DEBUG SERVER] Database result: {result}")
        
        if result['success']:
            response = {
                'type': RESP_SUCCESS,
                'success': True,
                'submission': result.get('submission')
            }
            # DEBUG: Print response (excluding file_data)
            if response.get('submission') and 'file_data' in response['submission']:
                debug_response = response.copy()
                debug_submission = debug_response['submission'].copy()
                debug_submission['file_data'] = f"<{len(response['submission']['file_data'])} bytes>"
                debug_response['submission'] = debug_submission
                print(f"[DEBUG SERVER] Sending SUCCESS response: {debug_response}")
            else:
                print(f"[DEBUG SERVER] Sending SUCCESS response: {response}")
            return response
        else:
            response = {'type': RESP_ERROR, 'success': False, 'error': result['error']}
            print(f"[DEBUG SERVER] Sending ERROR response: {response}")
            return response
    
    def handle_post_announcement(self, data):
        """Handle post announcement request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can post announcements'}
        
        class_id = data.get('class_id')
        title = data.get('title')
        content = data.get('content')
        file_path = data.get('file_path')
        
        result = self.db.post_announcement(
            class_id, data['user_id'], title, content, file_path
        )
        
        if result['success']:
            # Get class data and student emails for notifications
            class_data = self.db.get_class_by_id(class_id)
            if class_data['success'] and class_data['class']:
                class_info = class_data['class']
                student_emails = []
                
                # Get student emails from enrolled_students
                for student_id in class_info.get('enrolled_students', []):
                    student = self.db.get_user_by_id(student_id)
                    if student['success']:
                        student_emails.append(student['user'].get('email'))
                
                # Send notifications (email + TCP)
                announcement_data = {
                    'title': title,
                    'content': content,
                    'created_at': result.get('created_at', '')
                }
                self.notifier.notify_announcement_posted(class_info, announcement_data, student_emails)
            
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'announcement_id': result['announcement_id']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_view_announcements(self, data):
        """Handle view announcements request"""
        class_id = data.get('class_id')
        result = self.db.get_announcements(class_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'announcements': result['announcements']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_post_comment(self, data):
        """Handle post comment request"""
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        class_id = data.get('class_id')
        comment_text = data.get('comment_text')
        parent_comment_id = data.get('parent_comment_id')
        
        result = self.db.post_comment(
            item_id, item_type, class_id, data['user_id'], comment_text, parent_comment_id
        )
        
        if result['success']:
            # Get class data and student emails for notifications
            class_data = self.db.get_class_by_id(class_id)
            if class_data['success'] and class_data['class']:
                class_info = class_data['class']
                student_emails = []
                teacher_email = None
                
                # Get teacher email
                teacher_id = class_info.get('teacher_id')
                if teacher_id:
                    teacher = self.db.get_user_by_id(teacher_id)
                    if teacher['success']:
                        teacher_email = teacher['user'].get('email')
                
                # Get student emails from students
                for student_id in class_info.get('students', []):
                    student = self.db.get_user_by_id(student_id)
                    if student['success']:
                        student_emails.append(student['user'].get('email'))
                
                # Get commenter name
                commenter = self.db.get_user_by_id(data['user_id'])
                commenter_name = commenter['user']['name'] if commenter['success'] else 'Unknown'
                
                # Send notifications (email + TCP) to all class members (students + teacher)
                comment_data = {
                    'item_id': item_id,
                    'item_type': item_type,
                    'comment_text': comment_text,
                    'commenter_name': commenter_name,
                    'created_at': result.get('created_at', '')
                }
                
                # Combine all recipient IDs (students + teacher)
                all_recipient_ids = class_info.get('students', []).copy()
                if teacher_id:
                    all_recipient_ids.append(teacher_id)
                
                # Combine all emails for email notifications
                all_emails = student_emails.copy()
                if teacher_email:
                    all_emails.append(teacher_email)
                
                self.notifier.notify_comment_posted(class_info, comment_data, all_recipient_ids)
            
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'comment_id': result['comment_id']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_view_comments(self, data):
        """Handle view comments request"""
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        result = self.db.get_comments(item_id, item_type)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'comments': result['comments']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_download_file(self, data, client_socket, address):
        """Handle file download request - use same protocol as other messages"""
        file_id = data.get('file_id')
        request_id = data.get('request_id')

        if not file_id:
            return {'type': RESP_ERROR, 'error': 'File ID required'}

        result = self.db.download_material_gridfs(file_id)

        if result['success']:
            # Get file content
           file_content = result['file_content']
           filename = result.get('filename', 'download.bin')
           size = len(file_content)
    
           print(f"[SERVER DOWNLOAD] Sending file: {filename}, size: {size} bytes")
    
           # Create metadata
           metadata = {
               'type': RESP_SUCCESS,
               'success': True,
               'filename': filename,
               'content_type': result.get('content_type', 'application/octet-stream'),
               'size': size
           }
        
           if request_id:
               metadata['request_id'] = request_id
    
           # Send metadata using length-prefixed protocol (same as all other messages)
           json_data = json.dumps(metadata).encode()
           length_prefix = len(json_data).to_bytes(4, byteorder='big')
        
           # Send metadata
           client_socket.sendall(length_prefix + json_data)
        
           # Send binary data immediately after
           print(f"[SERVER DOWNLOAD] Now sending {size} bytes of raw binary...")
           client_socket.sendall(file_content)
        
           print(f"[SERVER DOWNLOAD] File sent successfully")
        
           # FIX: Return a proper response, not None
           return {
               'type': RESP_SUCCESS,
               'success': True,
               'message': 'File sent successfully',
               'filename': filename,
               'size': size
           }
    
        else:
           return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
 
    
    def handle_remove_student(self, data):
        """Handle remove student request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can remove students'}
        
        class_id = data.get('class_id')
        student_id = data.get('student_id')
        
        result = self.db.remove_student(class_id, student_id)
        
        if result['success']:
            return {'type': RESP_SUCCESS, 'success': True}
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_delete_class(self, data):
        """Handle delete class request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can delete classes'}
        
        class_id = data.get('class_id')
        result = self.db.delete_class(class_id)
        
        if result['success']:
            return {'type': RESP_SUCCESS, 'success': True}
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_view_students(self, data):
        """Handle view students request"""
        class_id = data.get('class_id')
        result = self.db.get_class_students(class_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'students': result['students']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
        

    
    def handle_upload_material(self, data):
       """Handle upload material request"""
       if data['user_role'] != 'teacher':
           return {'type': RESP_ERROR, 'error': 'Only teachers can upload materials'}
    
       class_id = data.get('class_id')
       title = data.get('title')
       material_type = data.get('material_type', 'Document')
       file_content = data.get('file_data')  # This should be binary data from the frontend
    
       result = self.db.upload_material(class_id, data['user_id'], title, material_type, file_content)
    
       if result['success']:
           # Send notifications about the uploaded material
           return {
               'type': RESP_SUCCESS,
               'success': True,
               'material_id': result['material_id']
           }
       else:
           return {'type': RESP_ERROR, 'success': False, 'error': result['error']}


    
    def handle_view_materials(self, data):
        """Handle view materials request"""
        class_id = data.get('class_id')
        result = self.db.get_materials(class_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'materials': result['materials']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_get_teacher_submissions(self, data):
        """Handle get all teacher's submissions request"""
        if data['user_role'] != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can view all submissions'}
        
        teacher_id = data['user_id']
        result = self.db.get_teacher_submissions(teacher_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'submissions': result['submissions']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_get_student_all_assignments(self, data):
        """Handle get all student's assignments request"""
        if data['user_role'] != 'student':
            return {'type': RESP_ERROR, 'error': 'Only students can view their assignments'}
        
        student_id = data['user_id']
        result = self.db.get_student_all_assignments(student_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'assignments': result['assignments']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
    
    def handle_get_notifications(self, data):
        """Handle get notifications request"""
        user_id = data.get('user_id')
        
        result = self.db.get_user_notifications(user_id)
        
        if result['success']:
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'notifications': result['notifications']
            }
        else:
            return {'type': RESP_ERROR, 'success': False, 'error': result['error']}
        
    def handle_submit_assignment_gridfs(self, data, client_socket, address):
        """Handle GridFS-based assignment submission with binary protocol"""
        if data['user_role'] != 'student':
            return {'type': RESP_ERROR, 'error': 'Only students can submit assignments'}
    
        assignment_id = data.get('assignment_id')
        user_id = data.get('user_id')
        submission_text = data.get('submission_text', '')
        filename = data.get('filename', '')
        expected_file_size = data.get('file_size', 0)
    
        print(f"[SERVER GRIDFS] Starting GridFS submission from {address}")
        print(f"  Assignment ID: {assignment_id}")
        print(f"  User ID: {user_id}")
        print(f"  Filename: {filename}")
        print(f"  Expected file size: {expected_file_size} bytes")
    
        try:
            # Read binary data directly from socket
            file_content = b""
            bytes_received = 0
        
            # Read the binary data that follows the JSON message
            while bytes_received < expected_file_size:
                chunk_size = min(4096, expected_file_size - bytes_received)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    print(f"  ❌ Connection closed prematurely")
                    break
                file_content += chunk
                bytes_received += len(chunk)
        
            print(f"[SERVER GRIDFS] Received {len(file_content)} bytes of binary data")
         
            # Verify we got all data
            if len(file_content) != expected_file_size:
                print(f"  ⚠️ Warning: Expected {expected_file_size} bytes, got {len(file_content)}")
        
            # Now call the database handler for GridFS storage
            result = self.db.submit_assignment_gridfs(
                assignment_id, user_id, file_content, submission_text, filename
            )
        
            if result['success']:
                print(f"  ✅ GridFS submission successful: {result['submission_id']}")
            
                # Send success response
                return {
                    'type': RESP_SUCCESS,
                    'success': True,
                    'submission_id': result['submission_id'],
                    'file_id': result.get('file_id'),
                    'message': 'Assignment submitted successfully to GridFS'
                }
            else:
                print(f"  ❌ GridFS submission failed: {result['error']}")
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': result['error']
                }
            
        except Exception as e:
            print(f"  ❌ GridFS handler error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': f'GridFS submission failed: {str(e)}'
            }
        
    def handle_upload_material_gridfs(self, data, client_socket, address):
        """Handle GridFS-based material upload with binary protocol"""
        if data.get('user_role') != 'teacher':
            return {'type': RESP_ERROR, 'error': 'Only teachers can upload materials'}
    
        class_id = data.get('class_id')
        teacher_id = data.get('teacher_id')
        title = data.get('title')
        material_type = data.get('material_type', 'Document')
        filename = data.get('filename', '')
        expected_file_size = data.get('file_size', 0)
    
        print(f"[SERVER MATERIAL GRIDFS] Starting material upload from {address}")
        print(f"  Class ID: {class_id}")
        print(f"  Teacher ID: {teacher_id}")
        print(f"  Title: {title}")
        print(f"  Filename: {filename}")
        print(f"  Expected file size: {expected_file_size} bytes")
    
        try:
            # Read binary data directly from socket
            file_content = b""
            bytes_received = 0
        
            # Read the binary data that follows the JSON message
            while bytes_received < expected_file_size:
                chunk_size = min(4096, expected_file_size - bytes_received)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    print(f"  ❌ Connection closed prematurely")
                    break
                file_content += chunk
                bytes_received += len(chunk)
        
            print(f"[SERVER MATERIAL GRIDFS] Received {len(file_content)} bytes of binary data")
        
            # Verify we got all data
            if len(file_content) != expected_file_size:
                print(f"  ⚠️ Warning: Expected {expected_file_size} bytes, got {len(file_content)}")
        
            # Call the database handler for GridFS storage
            result = self.db.upload_material_gridfs(
                class_id, teacher_id, title, material_type, file_content, filename
            )
        
            if result['success']:
                print(f"  ✅ Material upload successful: {result['material_id']}")
            
                # Send success response
                return {
                    'type': RESP_SUCCESS,
                    'success': True,
                    'material_id': result['material_id'],
                    'file_id': result.get('file_id'),
                    'message': 'Material uploaded successfully to GridFS'
                }
            else:
                print(f"  ❌ Material upload failed: {result['error']}")
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': result['error']
                }
            
        except Exception as e:
            print(f"  ❌ Material upload handler error: {e}")
            import traceback
            traceback.print_exc()
            return {
               'type': RESP_ERROR,
               'success': False,
                'error': f'Material upload failed: {str(e)}'
            }
    

    
    def stop(self):
        """Stop the server"""
        print("\n🛑 Shutting down server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("✅ Server stopped\n")


if __name__ == '__main__':
    server = LearnLiveServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt received")
        server.stop()
