# LearnLive - TCP-Based Classroom Management System

A desktop classroom management application built with Python TCP sockets, similar to Google Classroom, for managing classes, assignments, announcements, and materials.

## 🎓 Features

### Teacher Features:

- ✅ Login/Signup
- ✅ Create and manage classes
- ✅ Create assignments with due dates
- ✅ View and download student submissions
- ✅ Post class announcements
- ✅ Upload class materials (PDFs, documents, images)
- ✅ Remove or kick students from classes
- ✅ View enrolled students
- ✅ Reply to student comments
- ✅ Archive or delete classes

### Student Features:

- ✅ Login/Signup
- ✅ Join classes using class code
- ✅ View enrolled classes
- ✅ View and submit assignments
- ✅ Download class materials
- ✅ View announcements
- ✅ Comment on announcements
- ✅ View classmates
- ✅ Receive email notifications

## 🔧 Technology Stack

- **Backend**: Python 3.x with TCP socket programming
- **Frontend**: Python + ttkbootstrap (modern Tkinter GUI)
- **Database**: MongoDB with PyMongo
- **Notifications**: Gmail SMTP (smtplib)
- **Architecture**: Multi-threaded TCP server

## 🌐 Networking Concepts Demonstrated

This project demonstrates key networking concepts:

### 1. **TCP Socket Programming**

- Connection-oriented communication
- Reliable, ordered data delivery
- Custom application-layer protocol

### 2. **Multi-threading**

- Concurrent client handling
- Thread-per-client model
- Synchronized access to shared resources

### 3. **Custom Protocol Design**

- JSON-based message format
- Request-response pattern
- Token-based authentication

### 4. **File Transfer Protocol**

- Chunked binary file transfer
- Progress tracking
- File validation and integrity

### 5. **Client-Server Architecture**

- Central server coordination
- Session management
- Token-to-socket mapping

### 6. **SMTP Protocol**

- Email notifications
- Gmail SMTP integration
- Asynchronous notifications

## 📁 Project Structure

```
LearnLive/
├── config/
│   ├── __init__.py
│   └── config.py              # Configuration settings
├── server/
│   ├── __init__.py
│   ├── server.py              # Main TCP server
│   ├── database.py            # MongoDB operations
│   ├── file_handler.py        # File transfer handler
│   └── notification.py        # Email notifications
├── client/                     # (To be implemented)
│   ├── client.py              # TCP client connection
│   ├── main_gui.py            # Main GUI window
│   ├── login_gui.py           # Login/Signup interface
│   ├── teacher_dashboard.py  # Teacher interface
│   └── student_dashboard.py  # Student interface
├── uploads/                   # File upload directory
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- MongoDB installed and running
- Gmail account (for SMTP notifications)

### Installation Steps

1. **Clone the repository**

```bash
cd LearnLive
```

2. **Create virtual environment** (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Setup MongoDB**

- Install MongoDB: https://www.mongodb.com/try/download/community
- Start MongoDB service:

```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Windows
# MongoDB runs as a service automatically
```

5. **Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` file with your settings:

```
MONGODB_URI=mongodb://localhost:27017/
SMTP_EMAIL=your-email@gmail.com
SMTP_APP_PASSWORD=your-16-character-app-password
SECRET_KEY=your-secret-key
```

**Gmail SMTP Setup:**

1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App Passwords
4. Generate app password for "Mail"
5. Use this 16-character password in `.env`

6. **Create uploads directory**

```bash
mkdir uploads
```

## ▶️ Running the Application

### Start the Server

```bash
python server/server.py
```

You should see:

```
🎓 LearnLive Server Initializing...
📡 Host: 0.0.0.0
🔌 Port: 8888
✅ Database connected successfully
📁 File handler initialized
📧 Notification handler initialized

✅ Server started successfully!
🌐 Listening on 0.0.0.0:8888
👥 Max clients: 50
📦 Buffer size: 4096 bytes

⏳ Waiting for connections...
```

### Start the Client (GUI)

```bash
python client/main_gui.py  # (To be implemented)
```

## 📡 TCP Protocol Specification

### Message Format

All messages are JSON objects sent over TCP:

```json
{
  "type": "MESSAGE_TYPE",
  "token": "user_session_token",
  "data": {
    // Message-specific data
  }
}
```

### Message Types

**Authentication:**

- `LOGIN` - User login
- `SIGNUP` - User registration

**Class Management:**

- `CREATE_CLASS` - Create new class
- `JOIN_CLASS` - Join class with code
- `VIEW_CLASSES` - Get user's classes
- `VIEW_STUDENTS` - Get class students
- `REMOVE_STUDENT` - Remove student from class
- `DELETE_CLASS` - Delete class

**Assignments:**

- `CREATE_ASSIGNMENT` - Create assignment
- `VIEW_ASSIGNMENTS` - Get class assignments
- `SUBMIT_ASSIGNMENT` - Submit assignment
- `VIEW_SUBMISSIONS` - View student submissions

**Announcements:**

- `POST_ANNOUNCEMENT` - Post announcement
- `VIEW_ANNOUNCEMENTS` - Get announcements
- `POST_COMMENT` - Comment on announcement
- `VIEW_COMMENTS` - Get comments

**File Transfer:**

- `START_FILE_TRANSFER` - Initiate upload
- `FILE_CHUNK` - Send file chunk
- `END_FILE_TRANSFER` - Complete upload
- `UPLOAD_MATERIAL` - Upload class material
- `VIEW_MATERIALS` - Get class materials

### Response Format

```json
{
  "type": "SUCCESS" | "ERROR" | "NOTIFICATION",
  "success": true | false,
  "data": {},
  "error": "error message"  // if error
}
```

## 🔒 Security Features

- Password hashing (SHA-256)
- Token-based session management
- File size and type validation
- Input sanitization
- Secure SMTP with TLS

## 🌍 Network Configuration

### LAN Setup (Default)

The server listens on `0.0.0.0:8888` by default, accessible from:

- Same computer: `127.0.0.1:8888`
- Local network: `192.168.x.x:8888`

### Port Configuration

Edit `config/config.py` to change:

```python
SERVER_PORT = 8888  # Change to desired port
```

### Firewall Settings

Ensure port 8888 is open:

```bash
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /path/to/python

# Linux (ufw)
sudo ufw allow 8888/tcp
```

## 📊 Networking Concepts - Detailed Explanation

### TCP 3-Way Handshake

```
Client                    Server
  |                          |
  |--- SYN ----------------->|
  |<-- SYN-ACK --------------|
  |--- ACK ----------------->|
  |                          |
  | Connection Established   |
```

### Multi-threaded Server Architecture

```
Main Thread (Accept Loop)
    │
    ├── Client Thread 1 (User A)
    ├── Client Thread 2 (User B)
    ├── Client Thread 3 (User C)
    └── ...
```

### File Transfer Protocol

```
1. Client → START_FILE_TRANSFER (metadata)
2. Server → ACK (ready)
3. Client → CHUNK_1 (binary data)
4. Client → CHUNK_2 (binary data)
5. Client → ...
6. Client → END_FILE_TRANSFER
7. Server → SUCCESS (file saved)
```

## 🧪 Testing

### Test Server Connection

```bash
python
>>> import socket
>>> s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
>>> s.connect(('127.0.0.1', 8888))
>>> print("Connected!")
```

### Test Authentication

```python
import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 8888))

# Login request
msg = {
    "type": "LOGIN",
    "data": {
        "email": "teacher@example.com",
        "password": "password123"
    }
}

s.send(json.dumps(msg).encode())
response = json.loads(s.recv(4096).decode())
print(response)
```

## 📝 TODO

- [ ] Implement client GUI with ttkbootstrap
- [ ] Add file download functionality
- [ ] Implement real-time notifications in GUI
- [ ] Add assignment deadline reminders
- [ ] Implement class analytics dashboard
- [ ] Add support for video materials
- [ ] Implement student performance tracking
- [ ] Add export functionality (grades, reports)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

**Ishrak Faisal**

- GitHub: [@ishrak100](https://github.com/ishrak100)

## 🎓 Academic Note

This project demonstrates networking concepts including:

- TCP socket programming
- Multi-threading
- Protocol design
- Client-server architecture
- File transfer protocols
- Email protocols (SMTP)

Perfect for computer networking lab projects!

---

**Built with 💻 for learning networking concepts**
