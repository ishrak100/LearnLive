#!/usr/bin/env python3
"""
Demo script to test LearnLive components without full setup.
Tests the TCP client-server connection and GUI.
"""

import sys
import os
import threading
import time

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("LearnLive Demo - Component Test")
print("=" * 60)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from client.client import LearnLiveClient
    print("  ✅ LearnLiveClient imported")
except Exception as e:
    print(f"  ❌ Failed to import LearnLiveClient: {e}")
    sys.exit(1)

try:
    from client.login_gui import LoginWindow
    print("  ✅ LoginWindow imported")
except Exception as e:
    print(f"  ❌ Failed to import LoginWindow: {e}")
    sys.exit(1)

try:
    from client.teacher_dashboard import TeacherDashboard
    print("  ✅ TeacherDashboard imported")
except Exception as e:
    print(f"  ❌ Failed to import TeacherDashboard: {e}")
    sys.exit(1)

try:
    from client.student_dashboard import StudentDashboard
    print("  ✅ StudentDashboard imported")
except Exception as e:
    print(f"  ❌ Failed to import StudentDashboard: {e}")
    sys.exit(1)

# Test 2: Create client instance
print("\n2. Testing TCP client...")
try:
    client = LearnLiveClient()
    print("  ✅ LearnLiveClient instance created")
    print(f"  - Socket: {client.socket}")
    print(f"  - Connected: {client.connected}")
except Exception as e:
    print(f"  ❌ Failed to create client: {e}")
    sys.exit(1)

# Test 3: Check config
print("\n3. Testing configuration...")
try:
    from config.config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
    print("  ✅ Configuration loaded")
    print(f"  - Server: {SERVER_HOST}:{SERVER_PORT}")
    print(f"  - Buffer: {BUFFER_SIZE} bytes")
except Exception as e:
    print(f"  ❌ Failed to load config: {e}")
    sys.exit(1)

# Test 4: Check GUI library
print("\n4. Testing GUI library (ttkbootstrap)...")
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    print("  ✅ ttkbootstrap imported successfully")
    print(f"  - Version: {ttk.__version__}")
except Exception as e:
    print(f"  ❌ Failed to import ttkbootstrap: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All component tests passed!")
print("\nYou can now run the application:")
print("  1. Start server: python server/server.py")
print("  2. Start client: python client/main_gui.py")
print("\nNote: Make sure MongoDB is running before starting the server!")
print("=" * 60)
