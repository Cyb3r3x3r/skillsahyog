# 🔁 SkillSahyog

A full-stack web application that enables users to discover, match, and exchange skills with others in a secure and user-friendly environment. Features AI-driven skill suggestions, real-time chat, and a powerful admin panel for platform moderation.

## ✨ Features

### 👥 User Features
- **Secure Authentication**: Email OTP-based signup, login, and password reset.
- **Profile Management**: Update bio, skills offered/needed, and view activity history.
- **Skill Matching**: AI-based user matching sorted by relevance and trust.
- **Skill Discovery**: Browse and filter users and skills based on popularity and authenticity.
- **Skill Exchange**: Send and manage exchange requests with real-time updates.
- **Real-Time Chat**: Date-wise conversation UI powered by polling.
- **Feedback System**: Rate and review users post skill exchange.
- **Notifications**: Instant alerts for requests, messages, and admin actions.
- **Skill Recommendations**: Trending skill suggestions based on profile and usage data.

### 🔧 Admin Features
- **Admin Dashboard**: Monitor flagged users and content.
- **Skill Moderation**: Approve or reject user-submitted skill listings.
- **Support Management**: View and resolve user-submitted support tickets.
- **User Management**: Block/delete users violating platform guidelines.

## 🛠️ Tech Stack

- **Backend**: Python, Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 
- **Database**: PostgreSQL
- **Caching/Queueing**: Redis (for chat, OTP, and notifications)
- **Real-time Chat**: Django Channels / long-polling fallback
- **AI Matching**: Custom logic using similarity ranking / ML-based sorting
- **Deployment**: Docker / Render

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Cyb3r3x3r/skillsahyog.git
   cd skill-exchange
   ```
Set up a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## 🔧 Running the Application

### 📦 Option 1: Using Supervisord (Recommended for Multi-process Setup)

Ensure all Python dependencies are installed:
Then start the server using supervisord:

```bash
supervisord -c supervisord.conf
```
This will launch:

🟢 Django development server on http://localhost:8000

🟢 Daphne ASGI server on http://localhost:8001 (for async features like WebSockets)

### 💻 Option 2: Run Locally for Development (Without Supervisord)
#### Terminal 1: Use Django's Dev Server (Simple, for testing)
```bash
python manage.py runserver 0.0.0.0:8000
```

#### Terminal 2: Use Daphne ASGI Server (For WebSocket Support)
```bash
daphne -b 0.0.0.0 -p 8000 skillsahyog.asgi:application
```

Make sure daphne is installed via: pip install daphne

🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

📩 Contact
For questions, bugs, or suggestions: shivamraj878@gmail.com

© 2025 Cyb3r3x3r. Licensed under MIT.
