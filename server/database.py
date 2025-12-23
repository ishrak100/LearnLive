# Database Operations for LearnLive

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import hashlib
import secrets
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *


class Database:
    def __init__(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DATABASE_NAME]
            
            # Collections
            self.users = self.db[USERS_COLLECTION]
            self.classes = self.db[CLASSES_COLLECTION]
            self.assignments = self.db[ASSIGNMENTS_COLLECTION]
            self.submissions = self.db[SUBMISSIONS_COLLECTION]
            self.announcements = self.db[ANNOUNCEMENTS_COLLECTION]
            self.comments = self.db[COMMENTS_COLLECTION]
            self.materials = self.db[MATERIALS_COLLECTION]
            self.notifications = self.db['notifications']
            
            # Create indexes for performance
            self.users.create_index('email', unique=True)
            self.classes.create_index('class_code', unique=True)
            self.announcements.create_index([('class_id', 1), ('created_at', -1)])  # Speed up announcement queries
            self.notifications.create_index([('user_id', 1), ('created_at', -1)])  # Speed up notification queries
            
            print("✅ Database connected successfully")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            raise
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_token(self):
        """Generate a unique session token"""
        return secrets.token_urlsafe(32)
    
    def generate_class_code(self):
        """Generate a unique 6-character class code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not self.classes.find_one({'class_code': code}):
                return code
    
    # ========== USER OPERATIONS ==========
    
    def create_user(self, email, password, name, role):
        """Create a new user (teacher or student)"""
        try:
            hashed_password = self.hash_password(password)
            user = {
                'email': email,
                'password': hashed_password,
                'name': name,
                'role': role,  # 'teacher' or 'student'
                'created_at': datetime.now()
            }
            result = self.users.insert_one(user)
            return {'success': True, 'user_id': str(result.inserted_id)}
        except Exception as e:
            error_msg = str(e)
            # Make duplicate key error user-friendly
            if 'E11000 duplicate key' in error_msg and 'email' in error_msg:
                error_msg = 'Email already registered. Please use a different email or login.'
            return {'success': False, 'error': error_msg}
    
    def authenticate_user(self, email, password):
        """Authenticate user and return user data"""
        try:
            hashed_password = self.hash_password(password)
            user = self.users.find_one({'email': email, 'password': hashed_password})
            if user:
                token = self.generate_token()
                # Store token in user document
                self.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'token': token, 'last_login': datetime.now()}}
                )
                return {
                    'success': True,
                    'user_id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role'],
                    'token': token
                }
            return {'success': False, 'error': 'Invalid credentials'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_token(self, token):
        """Verify session token and return user data"""
        try:
            user = self.users.find_one({'token': token})
            if user:
                return {
                    'success': True,
                    'user_id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role']
                }
            return {'success': False, 'error': 'Invalid token'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== CLASS OPERATIONS ==========
    
    def create_class(self, teacher_id, class_name, section='', subject='', room='', description=''):
        """Create a new class"""
        try:
            class_code = self.generate_class_code()
            class_data = {
                'class_name': class_name,
                'section': section,
                'subject': subject,
                'room': room,
                'description': description,
                'class_code': class_code,
                'teacher_id': teacher_id,
                'students': [],
                'created_at': datetime.now()
            }
            result = self.classes.insert_one(class_data)
            return {
                'success': True,
                'class_id': str(result.inserted_id),
                'class_code': class_code
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def join_class(self, student_id, class_code):
        """Student joins a class using class code"""
        try:
            class_data = self.classes.find_one({'class_code': class_code})
            if not class_data:
                return {'success': False, 'error': 'Invalid class code'}
            
            if student_id in class_data.get('students', []):
                return {'success': False, 'error': 'Already enrolled in this class'}
            
            self.classes.update_one(
                {'class_code': class_code},
                {'$push': {'students': student_id}}
            )
            return {'success': True, 'class_id': str(class_data['_id'])}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_classes(self, user_id, role):
        """Get all classes for a user (teacher or student)"""
        try:
            if role == 'teacher':
                classes = list(self.classes.find({'teacher_id': user_id}))
            else:
                classes = list(self.classes.find({'students': user_id}))
            
            # Convert ObjectId and datetime to string for JSON serialization
            # Also add teacher name and student names
            for c in classes:
                c['_id'] = str(c['_id'])
                if 'created_at' in c and c['created_at']:
                    # Check if it's a datetime object before calling isoformat
                    if isinstance(c['created_at'], datetime):
                        c['created_at'] = c['created_at'].isoformat()
                    # Otherwise it's already a string, keep it as is
                
                # Add teacher name
                if 'teacher_id' in c:
                    teacher = self.users.find_one({'_id': ObjectId(c['teacher_id'])})
                    if teacher:
                        c['teacher_name'] = teacher.get('name', 'Teacher')
                
                # Add student names
                student_list = []
                for student_id in c.get('students', []):
                    student = self.users.find_one({'_id': ObjectId(student_id)})
                    if student:
                        student_list.append({
                            'id': student_id,
                            'name': student.get('name', 'Student'),
                            'email': student.get('email', '')
                        })
                c['student_list'] = student_list
            
            return {'success': True, 'classes': classes}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_student(self, class_id, student_id):
        """Remove a student from a class"""
        try:
            self.classes.update_one(
                {'_id': class_id},
                {'$pull': {'students': student_id}}
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_class(self, class_id):
        """Delete a class"""
        try:
            self.classes.delete_one({'_id': class_id})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_class_students(self, class_id):
        """Get list of students in a class"""
        try:
            class_data = self.classes.find_one({'_id': class_id})
            if not class_data:
                return {'success': False, 'error': 'Class not found'}
            
            student_ids = class_data.get('students', [])
            students = []
            for sid in student_ids:
                from bson.objectid import ObjectId
                user = self.users.find_one({'_id': ObjectId(sid)})
                if user:
                    students.append({
                        'user_id': str(user['_id']),
                        'name': user['name'],
                        'email': user['email']
                    })
            
            return {'success': True, 'students': students}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== ASSIGNMENT OPERATIONS ==========
    
    def create_assignment(self, class_id, title, description, due_date, max_points=100):
        """Create a new assignment"""
        try:
            assignment = {
                'class_id': class_id,
                'title': title,
                'description': description,
                'due_date': due_date,
                'max_points': max_points,
                'created_at': datetime.now()
            }
            result = self.assignments.insert_one(assignment)
            return {'success': True, 'assignment_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_assignments(self, class_id):
        """Get all assignments for a class"""
        try:
            # Sort by created_at descending (newest first)
            assignments = list(self.assignments.find({'class_id': class_id}).sort('created_at', -1))
            for a in assignments:
                a['_id'] = str(a['_id'])
                # Set default max_points if not present (for old assignments)
                if 'max_points' not in a:
                    a['max_points'] = 100
                if 'created_at' in a and a['created_at']:
                    # Check if it's a datetime object before calling isoformat
                    if isinstance(a['created_at'], datetime):
                        a['created_at'] = a['created_at'].isoformat()
                    # Otherwise it's already a string, keep it as is
                if 'due_date' in a and a['due_date']:
                    # Check if it's a datetime object before calling isoformat
                    if isinstance(a['due_date'], datetime):
                        a['due_date'] = a['due_date'].isoformat()
                    # Otherwise it's already a string, keep it as is
            return {'success': True, 'assignments': assignments}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def submit_assignment(self, assignment_id, student_id, file_path, text_content=None):
        """Submit an assignment"""
        try:
            submission = {
                'assignment_id': assignment_id,
                'student_id': student_id,
                'file_path': file_path,
                'text_content': text_content,
                'submitted_at': datetime.now()
            }
            result = self.submissions.insert_one(submission)
            return {'success': True, 'submission_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_submissions(self, assignment_id):
        """Get all submissions for an assignment"""
        try:
            submissions = list(self.submissions.find({'assignment_id': assignment_id}))
            for s in submissions:
                s['_id'] = str(s['_id'])
                # Convert datetime to string for JSON serialization
                if 'submitted_at' in s and s['submitted_at']:
                    s['submitted_at'] = s['submitted_at'].isoformat()
                # Get student name
                from bson.objectid import ObjectId
                user = self.users.find_one({'_id': ObjectId(s['student_id'])})
                if user:
                    s['student_name'] = user['name']
            return {'success': True, 'submissions': submissions}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_student_submission(self, assignment_id, student_id):
        """Get a specific student's submission for an assignment"""
        try:
            submission = self.submissions.find_one({
                'assignment_id': assignment_id,
                'student_id': student_id
            })
            if submission:
                submission['_id'] = str(submission['_id'])
                return {'success': True, 'submission': submission}
            else:
                return {'success': False, 'error': 'No submission found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_teacher_submissions(self, teacher_id):
        """Get all submissions for all of teacher's assignments"""
        try:
            from bson.objectid import ObjectId
            
            # Get all classes taught by this teacher
            teacher_classes = list(self.classes.find({'teacher_id': teacher_id}))
            class_ids = [cls['_id'] for cls in teacher_classes]
            
            # Get all assignments for these classes
            assignments = list(self.assignments.find({'class_id': {'$in': [str(cid) for cid in class_ids]}}))
            assignment_ids = [str(assgn['_id']) for assgn in assignments]
            
            # Get all submissions for these assignments
            submissions = list(self.submissions.find({'assignment_id': {'$in': assignment_ids}}))
            
            # Enrich with student, assignment, and class info
            for s in submissions:
                s['_id'] = str(s['_id'])
                
                # Get student name
                user = self.users.find_one({'_id': ObjectId(s['student_id'])})
                if user:
                    s['student_name'] = user['name']
                
                # Get assignment title
                assignment = next((a for a in assignments if str(a['_id']) == s['assignment_id']), None)
                if assignment:
                    s['assignment_title'] = assignment['title']
                    
                    # Get class name
                    class_obj = next((c for c in teacher_classes if str(c['_id']) == assignment['class_id']), None)
                    if class_obj:
                        s['class_name'] = class_obj['class_name']
                
                # Format date
                if 'submitted_at' in s:
                    s['submitted_at'] = s['submitted_at'].strftime('%Y-%m-%d %H:%M')
            
            # Sort by submission date (newest first)
            submissions.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
            
            return {'success': True, 'submissions': submissions}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_student_all_assignments(self, student_id):
        """Get all assignments for all of student's classes"""
        try:
            from bson.objectid import ObjectId
            
            # Get all classes the student is enrolled in
            student_classes = list(self.classes.find({'students': student_id}))
            class_ids = [str(cls['_id']) for cls in student_classes]
            
            # Get all assignments for these classes
            assignments = list(self.assignments.find({'class_id': {'$in': class_ids}}))
            
            # Enrich with class info and submission status
            for assgn in assignments:
                assgn['_id'] = str(assgn['_id'])
                
                # Convert datetime to string for JSON serialization
                if 'created_at' in assgn and assgn['created_at']:
                    assgn['created_at'] = assgn['created_at'].isoformat()
                
                # Get class name
                class_obj = next((c for c in student_classes if str(c['_id']) == assgn['class_id']), None)
                if class_obj:
                    assgn['class_name'] = class_obj['class_name']
                
                # Check if student has submitted
                submission = self.submissions.find_one({
                    'assignment_id': str(assgn['_id']),
                    'student_id': student_id
                })
                assgn['submitted'] = submission is not None
                if submission and 'submitted_at' in submission:
                    assgn['submitted_at'] = submission['submitted_at'].isoformat()
            
            # Sort by creation date (newest first)
            assignments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return {'success': True, 'assignments': assignments}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== ANNOUNCEMENT OPERATIONS ==========
    
    def post_announcement(self, class_id, teacher_id, title, content, file_path=None):
        """Post an announcement"""
        try:
            announcement = {
                'class_id': class_id,
                'teacher_id': teacher_id,
                'title': title,
                'content': content,
                'file_path': file_path,
                'created_at': datetime.now()
            }
            result = self.announcements.insert_one(announcement)
            return {'success': True, 'announcement_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_announcements(self, class_id):
        """Get all announcements for a class"""
        try:
            announcements = list(self.announcements.find({'class_id': class_id}).sort('created_at', -1))
            for a in announcements:
                a['_id'] = str(a['_id'])
                if 'created_at' in a and a['created_at']:
                    # Check if it's a datetime object before calling isoformat
                    if isinstance(a['created_at'], datetime):
                        a['created_at'] = a['created_at'].isoformat()
                    # Otherwise it's already a string, keep it as is
            return {'success': True, 'announcements': announcements}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== COMMENT OPERATIONS ==========
    
    def post_comment(self, item_id, item_type, class_id, user_id, comment_text, parent_comment_id=None):
        """Post a comment on an item (announcement, assignment, or material)"""
        try:
            comment = {
                'item_id': item_id,
                'item_type': item_type,
                'class_id': class_id,
                'user_id': user_id,
                'comment_text': comment_text,
                'parent_comment_id': parent_comment_id,
                'created_at': datetime.now()
            }
            print(f"[DEBUG] Inserting comment: {comment}")
            result = self.comments.insert_one(comment)
            print(f"[DEBUG] Comment inserted with ID: {result.inserted_id}")
            return {'success': True, 'comment_id': str(result.inserted_id)}
        except Exception as e:
            print(f"[DEBUG] Error inserting comment: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_comments(self, item_id, item_type):
        """Get all comments for an item"""
        try:
            # Query for new schema comments only
            query = {'item_id': item_id, 'item_type': item_type}
            
            print(f"[DEBUG] Querying comments with: {query}")
            comments = list(self.comments.find(query).sort('created_at', -1))
            print(f"[DEBUG] Found {len(comments)} comments")
            
            for c in comments:
                print(f"[DEBUG] Processing comment: {c}")
                c['_id'] = str(c['_id'])
                
                # Handle backward compatibility for old comment structure
                if 'user_name' in c:
                    c['commenter_name'] = c['user_name']
                    del c['user_name']
                    print(f"[DEBUG] Renamed user_name to commenter_name")
                else:
                    # Get user name for new structure
                    from bson.objectid import ObjectId
                    user = self.users.find_one({'_id': ObjectId(c['user_id'])})
                    if user:
                        c['commenter_name'] = user['name']
                    else:
                        c['commenter_name'] = 'Unknown User'
                    print(f"[DEBUG] Set commenter_name from user lookup: {c['commenter_name']}")
                
                # Format timestamp and remove original datetime
                if isinstance(c['created_at'], datetime):
                    c['timestamp'] = c['created_at'].isoformat()
                    print(f"[DEBUG] Converted created_at to timestamp: {c['timestamp']}")
                else:
                    c['timestamp'] = str(c['created_at'])
                # Remove the datetime object to avoid JSON serialization issues
                if 'created_at' in c:
                    del c['created_at']
                    print(f"[DEBUG] Removed created_at field")
                
                print(f"[DEBUG] Processed comment: {c}")
            
            print(f"[DEBUG] Returning {len(comments)} processed comments")
            return {'success': True, 'comments': comments}
        except Exception as e:
            print(f"[DEBUG] Error getting comments: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========== MATERIAL OPERATIONS ==========
    
    def upload_material(self, class_id, teacher_id, title, material_type, file_path):
        """Upload class material"""
        try:
            material = {
                'class_id': class_id,
                'teacher_id': teacher_id,
                'title': title,
                'material_type': material_type,
                'file_path': file_path,
                'uploaded_at': datetime.now()
            }
            result = self.materials.insert_one(material)
            return {'success': True, 'material_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_materials(self, class_id):
        """Get all materials for a class"""
        try:
            materials = list(self.materials.find({'class_id': class_id}).sort('uploaded_at', -1))
            for m in materials:
                m['_id'] = str(m['_id'])
                # Convert datetime to string for JSON serialization
                if 'uploaded_at' in m and m['uploaded_at']:
                    m['uploaded_at'] = m['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')
            return {'success': True, 'materials': materials}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== HELPER METHODS FOR NOTIFICATIONS ==========
    
    def get_class_by_id(self, class_id):
        """Get class data by class ID"""
        try:
            from bson.objectid import ObjectId
            class_data = self.classes.find_one({'_id': ObjectId(class_id)})
            if class_data:
                class_data['_id'] = str(class_data['_id'])
                return {'success': True, 'class': class_data}
            return {'success': False, 'error': 'Class not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_by_id(self, user_id):
        """Get user data by user ID"""
        try:
            from bson.objectid import ObjectId
            user = self.users.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                return {'success': True, 'user': user}
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== NOTIFICATION METHODS ==========
    
    def save_notification(self, user_id, notification_data):
        """Save notification to database"""
        try:
            from bson.objectid import ObjectId
            notification = {
                'user_id': ObjectId(user_id),
                'type': notification_data.get('type'),
                'class_id': notification_data.get('class_id'),
                'class_name': notification_data.get('class_name'),
                'title': notification_data.get('announcement_title') or notification_data.get('assignment_title') or notification_data.get('material_title'),
                'data': notification_data,
                'read': False,
                'created_at': datetime.now().isoformat()
            }
            result = self.db.notifications.insert_one(notification)
            return {'success': True, 'notification_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_notifications(self, user_id, limit=50):
        """Get notifications for a user"""
        try:
            from bson.objectid import ObjectId
            notifications = list(self.db.notifications.find(
                {'user_id': ObjectId(user_id)}
            ).sort('created_at', -1).limit(limit))
            
            for notif in notifications:
                notif['_id'] = str(notif['_id'])
                notif['user_id'] = str(notif['user_id'])
            
            return {'success': True, 'notifications': notifications}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            from bson.objectid import ObjectId
            self.db.notifications.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {'read': True}}
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
