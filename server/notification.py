# Email Notification Handler using Gmail SMTP

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import sys
import os
from datetime import datetime
from bson.objectid import ObjectId

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *


class NotificationHandler:
    def __init__(self, db):
        """Initialize notification handler"""
        self.db = db
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_email = SMTP_EMAIL
        self.smtp_password = SMTP_PASSWORD
        self.online_clients = {}  # user_id -> (socket, user_data)
        print("📧 Notification handler initialized")
    
    def register_client(self, user_id, client_socket, user_data):
        """Register online client for real-time notifications"""
        self.online_clients[user_id] = (client_socket, user_data)
        print(f"🔔 User {user_id} registered for notifications")
        # Inform discussion handler about notifier so it can broadcast
        try:
            import server.discussion_handler as dh
            if hasattr(dh, 'set_notifier'):
                dh.set_notifier(self)
        except Exception:
            # Not critical; if discussion handler isn't available we'll skip registration
            pass
    
    def unregister_client(self, user_id):
        """Unregister client"""
        if user_id in self.online_clients:
            del self.online_clients[user_id]
            print(f"🔕 User {user_id} unregistered from notifications")
    
    def send_tcp_notification(self, user_id, notification_data):
        """Send real-time TCP notification to online user"""
        if user_id in self.online_clients:
            try:
                socket, user_data = self.online_clients[user_id]
                message = {
                    'type': 'NOTIFICATION',
                    'notification': notification_data
                }
                message_data = json.dumps(message).encode()
                message_length = len(message_data)
                length_prefix = message_length.to_bytes(4, byteorder='big')
                socket.sendall(length_prefix + message_data)
                print(f"📲 TCP notification sent to user {user_id}")
                return True
            except Exception as e:
                print(f"❌ TCP notification error: {e}")
                self.unregister_client(user_id)
        return False
    
    def send_email(self, to_email, subject, body):
        """Send email notification via Gmail SMTP"""
        try:
            # Skip if credentials not configured
            if self.smtp_email == 'your-email@gmail.com' or not self.smtp_password or self.smtp_password == 'your-app-password':
                print(f"⚠️  Email not sent (SMTP not configured): {to_email} - {subject}")
                return False
            
            # Create message
            message = MIMEMultipart()
            message['From'] = self.smtp_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(message)
            
            print(f"✉️  Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def notify_assignment_created(self, class_data, assignment_data, student_emails):
        """
        Notify students when teacher creates new assignment
        Sends both email and TCP notifications
        """
        class_id = class_data.get('_id')
        class_name = class_data.get('class_name', 'Unknown Class')
        assignment_title = assignment_data.get('title', 'New Assignment')
        due_date = assignment_data.get('due_date', 'No due date')
        
        subject = f"📚 New Assignment: {assignment_title}"
        body = f"""
Hello Student,

A new assignment has been posted in your class!

Class: {class_name}
Assignment: {assignment_title}
Due Date: {due_date}

Login to LearnLive to view details and submit your work.

Best regards,
LearnLive Team
        """
        
        notification_data = {
            'type': 'NEW_ASSIGNMENT',
            'class_id': class_id,
            'class_name': class_name,
            'assignment_title': assignment_title,
            'due_date': due_date,
            'timestamp': assignment_data.get('created_at', '')
        }
        
        # Send to all students
        student_ids = class_data.get('students', [])
        
        for email in student_emails:
            # Send email notification
            self.send_email(email, subject, body)
        
        # Send TCP notifications to online students
        for student_id in student_ids:
            # Save notification to database for offline users
            self.db.save_notification(student_id, notification_data)
            
            # Send TCP notification if student is online
            result = self.send_tcp_notification(student_id, notification_data)
            if result:
                print(f"📲 Real-time assignment notification sent to student {student_id}")
        
        print(f"📧 Assignment notifications sent: {assignment_title}")
        return True
    
    def notify_announcement_posted(self, class_data, announcement_data, student_emails):
        """
        Notify students when teacher posts announcement
        Sends both email and TCP notifications
        """
        class_id = class_data.get('_id')
        class_name = class_data.get('class_name', 'Unknown Class')
        announcement_title = announcement_data.get('title', 'New Announcement')
        announcement_content = announcement_data.get('content', '')
        
        subject = f"📢 New Announcement: {announcement_title}"
        body = f"""
Hello Student,

A new announcement has been posted in your class!

Class: {class_name}
Title: {announcement_title}

{announcement_content[:200]}{"..." if len(announcement_content) > 200 else ""}

Login to LearnLive to view the full announcement.

Best regards,
LearnLive Team
        """
        
        notification_data = {
            'type': 'NEW_ANNOUNCEMENT',
            'class_id': class_id,
            'class_name': class_name,
            'announcement_title': announcement_title,
            'content_preview': announcement_content[:100],
            'timestamp': announcement_data.get('created_at', '')
        }
        
        # Send to all students
        for email in student_emails:
            # Send email notification
            self.send_email(email, subject, body)
        
        # Batch save notifications to database (faster than individual saves)
        student_ids = class_data.get('students', [])
        print(f"[DEBUG] Sending notifications to {len(student_ids)} students")
        
        # Save all notifications in batch (database operation)
        for student_id in student_ids:
            self.db.save_notification(student_id, notification_data)
        
        # Send TCP notifications to online students only (no blocking)
        online_count = 0
        for student_id in student_ids:
            result = self.send_tcp_notification(student_id, notification_data)
            if result:
                online_count += 1
        
        print(f"📧 Announcement notifications sent: {announcement_title} ({online_count}/{len(student_ids)} online)")
        return True
    
    def notify_comment_added(self, class_data, announcement_title, commenter_name, comment_text, recipient_emails):
        """
        Notify when someone adds a comment
        Sends both email and TCP notifications
        """
        class_name = class_data.get('class_name', 'Unknown Class')
        
        subject = f"💬 New Comment on: {announcement_title}"
        body = f"""
Hello,

{commenter_name} commented on an announcement in {class_name}:

Announcement: {announcement_title}
Comment: {comment_text[:200]}{"..." if len(comment_text) > 200 else ""}

Login to LearnLive to view and respond.

Best regards,
LearnLive Team
        """
        
        notification_data = {
            'type': 'NEW_COMMENT',
            'class_name': class_name,
            'announcement_title': announcement_title,
            'commenter_name': commenter_name,
            'comment_preview': comment_text[:100],
            'timestamp': ''
        }
        
        # Send to recipients
        for email in recipient_emails:
            self.send_email(email, subject, body)
        
        print(f"📧 Comment notifications sent for: {announcement_title}")
        return True
    
    def notify_material_uploaded(self, class_data, material_title, file_name, student_emails):
        """
        Notify students when teacher uploads material/file
        Sends both email and TCP notifications
        """
        class_name = class_data.get('class_name', 'Unknown Class')
        class_id = class_data.get('_id', '')
        
        subject = f"📎 New Material: {material_title}"
        body = f"""
Hello Student,

New learning material has been uploaded to your class!

Class: {class_name}
Material: {material_title}
File: {file_name}

Login to LearnLive to download and view the material.

Best regards,
LearnLive Team
        """
        
        notification_data = {
            'type': 'NEW_MATERIAL',
            'class_id': class_id,
            'class_name': class_name,
            'material_title': material_title,
            'file_name': file_name,
            'timestamp': ''
        }
        
        # Send email to all students
        for email in student_emails:
            self.send_email(email, subject, body)
        
        # Get student IDs and send TCP notifications to online students
        student_ids = class_data.get('students', [])
        
        # Save all notifications in batch (database operation)
        for student_id in student_ids:
            self.db.save_notification(student_id, notification_data)
        
        # Send TCP notifications to online students only
        online_count = 0
        for student_id in student_ids:
            result = self.send_tcp_notification(student_id, notification_data)
            if result:
                online_count += 1
        
        print(f"📧 Material upload notifications sent: {material_title} ({online_count}/{len(student_ids)} online)")
        return True
    
    def notify_student_joined(self, class_code, student_email):
        """Notify teacher when student joins class"""
        subject = f"New Student Joined Class {class_code}"
        body = f"""
A new student has joined your class!

Student: {student_email}
Class Code: {class_code}

Login to LearnLive to view details.
        """
        # Note: In production, you'd get teacher email from database
        # For now, we'll skip actual sending in development
        print(f"📧 Notification: Student joined - {student_email}")
        return True
    
    def notify_new_assignment(self, class_id, assignment_title):
        """Notify students of new assignment"""
        subject = f"New Assignment: {assignment_title}"
        body = f"""
A new assignment has been posted in your class!

Assignment: {assignment_title}

Login to LearnLive to view details and submit.
        """
        print(f"📧 Notification: New assignment - {assignment_title}")
        return True
    
    def notify_new_submission(self, assignment_id, student_email):
        """Notify teacher of new submission"""
        try:
            # Get assignment details to find the teacher
            assignment = self.db.assignments.find_one({'_id': ObjectId(assignment_id)})
            if not assignment:
                print(f"❌ Assignment not found: {assignment_id}")
                return False
            
            # Get class details to find the teacher
            class_data = self.db.classes.find_one({'_id': assignment['class_id']})
            if not class_data:
                print(f"❌ Class not found for assignment")
                return False
            
            teacher_id = class_data.get('teacher_id')
            if not teacher_id:
                print(f"❌ Teacher not found for class")
                return False
            
            # Create notification data
            notification_data = {
                'type': 'NEW_SUBMISSION',
                'assignment_id': assignment_id,
                'assignment_title': assignment.get('title', 'Assignment'),
                'class_name': class_data.get('class_name', 'Unknown Class'),
                'student_email': student_email,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save notification to database for offline teacher
            self.db.save_notification(teacher_id, notification_data)
            
            # Send TCP notification if teacher is online
            result = self.send_tcp_notification(teacher_id, notification_data)
            if result:
                print(f"📲 Real-time submission notification sent to teacher {teacher_id}")
            else:
                print(f"💾 Submission notification saved for offline teacher {teacher_id}")
            
            print(f"📧 Notification: New submission from {student_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error notifying submission: {e}")
            return False
    
    def notify_new_announcement(self, class_id, announcement_title):
        """Notify students of new announcement"""
        subject = f"New Announcement: {announcement_title}"
        body = f"""
A new announcement has been posted in your class!

Title: {announcement_title}

Login to LearnLive to view details.
        """
        print(f"📧 Notification: New announcement - {announcement_title}")
        return True
    
    def notify_comment_posted(self, class_data, comment_data, recipient_ids):
        """
        Notify all class members (students + teacher) when someone posts a comment
        Sends both email and TCP notifications
        """
        class_id = class_data.get('_id')
        class_name = class_data.get('class_name', 'Unknown Class')
        item_type = comment_data.get('item_type', 'item')
        commenter_name = comment_data.get('commenter_name', 'Someone')
        comment_text = comment_data.get('comment_text', '')
        
        subject = f"💬 New Comment on {item_type.title()}"
        body = f"""
Hello,

{commenter_name} commented on a {item_type} in your class!

Class: {class_name}
Comment: {comment_text[:200]}{"..." if len(comment_text) > 200 else ""}

Login to LearnLive to view the full comment and reply.

Best regards,
LearnLive Team
        """
        
        notification_data = {
            'type': 'NEW_COMMENT',
            'class_id': class_id,
            'class_name': class_name,
            'item_type': item_type,
            'item_id': comment_data.get('item_id'),
            'commenter_name': commenter_name,
            'comment_preview': comment_text[:100],
            'timestamp': comment_data.get('created_at', '')
        }
        
        # Get recipient emails and send email notifications
        recipient_emails = []
        for recipient_id in recipient_ids:
            recipient = self.db.get_user_by_id(recipient_id)
            if recipient['success']:
                email = recipient['user'].get('email')
                if email:
                    recipient_emails.append(email)
                    # Send email notification
                    self.send_email(email, subject, body)
        
        print(f"[DEBUG] Sending comment notifications to {len(recipient_ids)} recipients")
        
        # Save all notifications to database
        for recipient_id in recipient_ids:
            self.db.save_notification(recipient_id, notification_data)
        
        # Send TCP notifications to online recipients only
        online_count = 0
        for recipient_id in recipient_ids:
            result = self.send_tcp_notification(recipient_id, notification_data)
            if result:
                online_count += 1
        
        print(f"💬 Comment notifications sent: {commenter_name} on {item_type} ({online_count}/{len(recipient_ids)} online)")
        return True
