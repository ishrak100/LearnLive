#!/usr/bin/env python3
"""
Check if all requirements are met to run LearnLive.
"""

import sys
import os

def check_imports():
    """Check if all required packages are installed."""
    print("Checking Python packages...")
    
    packages = [
        ('ttkbootstrap', 'ttkbootstrap'),
        ('pymongo', 'pymongo'),
        ('smtplib', 'smtplib'),
        ('dotenv', 'python-dotenv'),
        ('socket', 'socket'),
        ('json', 'json'),
        ('threading', 'threading'),
    ]
    
    all_ok = True
    for module_name, package_name in packages:
        try:
            __import__(module_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - Missing!")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists."""
    print("\nChecking environment file...")
    
    if os.path.exists('.env'):
        print("  ✅ .env file exists")
        
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'MONGODB_URI=' in content:
            print("  ✅ MONGODB_URI configured")
        else:
            print("  ⚠️  MONGODB_URI not set")
            
        if 'SMTP_EMAIL=' in content:
            print("  ✅ SMTP_EMAIL configured")
        else:
            print("  ⚠️  SMTP_EMAIL not set")
            
        return True
    else:
        print("  ❌ .env file not found")
        print("  Run: cp .env.example .env")
        return False

def check_mongodb():
    """Check if MongoDB is accessible."""
    print("\nChecking MongoDB connection...")
    
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        load_dotenv()
        
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=2000)
        
        # Trigger connection
        client.server_info()
        
        print(f"  ✅ Connected to MongoDB at {mongodb_uri}")
        return True
    except Exception as e:
        print(f"  ❌ MongoDB connection failed: {e}")
        print("\n  To start MongoDB:")
        print("    macOS: brew services start mongodb-community")
        print("    Linux: sudo systemctl start mongod")
        return False

def check_directories():
    """Check if required directories exist."""
    print("\nChecking directories...")
    
    dirs = ['server', 'client', 'config', 'uploads']
    all_ok = True
    
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - Missing!")
            all_ok = False
    
    return all_ok

def main():
    """Run all checks."""
    print("=" * 60)
    print("LearnLive - System Requirements Check")
    print("=" * 60)
    
    checks = [
        check_imports(),
        check_env_file(),
        check_directories(),
        check_mongodb(),
    ]
    
    print("\n" + "=" * 60)
    
    if all(checks):
        print("✅ All checks passed! You're ready to run LearnLive!")
        print("\nTo start:")
        print("  1. Run server: python server/server.py")
        print("  2. Run client: python client/main_gui.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
