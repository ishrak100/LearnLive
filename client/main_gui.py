#!/usr/bin/env python3
"""
LearnLive Client Application
Main entry point for the desktop GUI client.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import LearnLiveClient
from client.login_gui import LoginWindow
from client.teacher_dashboard import TeacherDashboard
from client.student_dashboard import StudentDashboard

def main():
    """Main application entry point."""
    # Create client instance
    client = LearnLiveClient()
    
    def on_login_success(user_data: dict):
        """
        Handle successful login.
        
        Args:
            user_data: User information from server
        """
        role = user_data.get("role", "student")
        
        # Show appropriate dashboard based on role
        if role == "teacher":
            dashboard = TeacherDashboard(client, user_data)
            dashboard.show()
        else:
            dashboard = StudentDashboard(client, user_data)
            dashboard.show()
    
    # Show login window
    login = LoginWindow(client, on_login_success)
    login.show()

if __name__ == "__main__":
    main()
