# Quick Start Guide

## Prerequisites

**Important:** This project requires Python with tkinter support. Python 3.13 might not have tkinter pre-installed.

### Install Python with tkinter (macOS):

```bash
# Using Homebrew
brew install python-tk@3.12

# Or install tkinter for Python 3.13
brew install tcl-tk
```

### Verify tkinter:

```bash
python3 -c "import tkinter; print('tkinter works!')"
```

## Step 1: Install Dependencies

```bash
# Navigate to project directory
cd /Users/ishrakfaisal/Desktop/LearnLive

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

## Step 2: Setup Environment

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` with your settings:

```
MONGODB_URI=mongodb://localhost:27017/
SMTP_EMAIL=your-email@gmail.com
SMTP_APP_PASSWORD=your-app-password
SECRET_KEY=your-secret-key-here
```

### Gmail SMTP Setup:

1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Go to App Passwords
4. Generate password for "Mail"
5. Use that 16-character password in `.env`

## Step 3: Start MongoDB

```bash
# macOS
brew services start mongodb-community

# Or manually
mongod --dbpath /usr/local/var/mongodb
```

## Step 4: Run the Server

```bash
python server/server.py
```

You should see:

```
🎓 LearnLive Server Initializing...
✅ Server started successfully!
🌐 Listening on 0.0.0.0:8888
```

## Step 5: Run the Client (in a new terminal)

```bash
# Activate virtual environment
source venv/bin/activate

# Run client GUI
python client/main_gui.py
```

## Testing

### Test with Two Users

1. **Create Teacher Account:**

   - Click "Sign Up"
   - Enter name, email, password
   - Select "Teacher" role
   - Click "Sign Up"

2. **Login as Teacher:**

   - Enter teacher email and password
   - Click "Login"
   - Create a class
   - Copy the class code

3. **Create Student Account (new terminal):**

   - Run another client: `python client/main_gui.py`
   - Click "Sign Up"
   - Enter name, email, password
   - Select "Student" role
   - Click "Sign Up"

4. **Login as Student:**
   - Enter student email and password
   - Click "Login"
   - Click "Join Class"
   - Enter the class code from teacher
   - Explore the class!

## Features to Test

### Teacher:

- ✅ Create classes
- ✅ Create assignments
- ✅ Post announcements
- ✅ Upload materials
- ✅ View students
- ✅ Remove students
- ✅ View submissions

### Student:

- ✅ Join classes
- ✅ View assignments
- ✅ Submit assignments
- ✅ Download materials
- ✅ View announcements
- ✅ Post comments
- ✅ View classmates

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8888
lsof -ti:8888

# Kill process
kill -9 <PID>
```

### MongoDB Connection Error

```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Restart MongoDB
brew services restart mongodb-community
```

### Import Errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## LAN Testing

1. Find your local IP:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

2. Edit `config/config.py`:

```python
SERVER_HOST = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 8888
```

3. Other computers can connect using:

   - Your IP address (e.g., 192.168.1.100)
   - Port 8888

4. Make sure firewall allows connections on port 8888

## Project Structure

```
LearnLive/
├── server/
│   ├── server.py           # Main TCP server
│   ├── database.py         # MongoDB operations
│   ├── file_handler.py     # File transfers
│   └── notification.py     # Email notifications
├── client/
│   ├── main_gui.py         # Client entry point
│   ├── client.py           # TCP client
│   ├── login_gui.py        # Login/Signup GUI
│   ├── teacher_dashboard.py # Teacher interface
│   └── student_dashboard.py # Student interface
├── config/
│   └── config.py           # Configuration settings
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## Networking Concepts Demonstrated

This project shows:

1. **TCP Socket Programming** - Client-server communication
2. **Multi-threading** - Concurrent client handling
3. **Custom Protocol** - JSON-over-TCP messages
4. **File Transfer** - Chunked binary transfers
5. **Session Management** - Token-based authentication
6. **SMTP Protocol** - Email notifications

Perfect for your networking lab project! 🎓
