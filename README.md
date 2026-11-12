# TaskFlow &bull; Smart Todo & Personal Schedule Planner

A modern, highly responsive Flask web application featuring user isolation, precise time allocation for scheduling, real-time reminder notifications with audio chimes, and an attractive custom CSS design system.

---

## ✨ Features

### 👤 Multi-User Privacy & Isolation
- **Secure Authentication**: User registration and login powered by Werkzeug secure password hashing (`generate_password_hash` & `check_password_hash`).
- **Data Isolation**: Each user gets their own private workspace. Users can only see, create, edit, and delete their own tasks.
- **Quick Demo Login**: Comes pre-configured with a demo account (`demo` / `password123`) for instant testing.

### ⏱️ Time Allocation & Proper Scheduling
- **Exact Time Slots**: Allocate both `Start Time` and `End Time` alongside a `Schedule Date` for any task.
- **Interactive Daily Schedule Timeline**: Switch between a card dashboard and a chronological hourly schedule timeline to view your day at a glance.
- **Task Prioritization**: Categorize tasks as `High` (Red), `Medium` (Yellow), or `Low` (Green) with visual badge accents.
- **Categories**: Tag items under Work, Personal, Study, Fitness, Finance, Urgent, or Other.

### 🔔 Smart Reminders & Real-Time Alerts
- **Custom Reminder Datetimes**: Set an exact reminder date and time (with presets: *At start time*, *15 mins before*, *1 hour before*).
- **In-App Toast Alerts**: Dynamic toast notifications appear when tasks become due.
- **Synthesized Audio Chimes**: Generates a gentle bell chime using the Web Audio API without needing external sound files.
- **Browser Desktop Notifications**: Supports standard Web Notifications API for background alerts across tabs.
- **One-Click Dismiss & Snooze**: Dismiss or complete tasks to silence reminders.

### 🎨 Attractive & Modern UI
- **Custom CSS Stylesheet** (`static/css/style.css`): Complete custom design system with CSS variables, subtle gradients, soft card elevation, and smooth transitions.
- **Dashboard Overview Metrics**: Live statistic cards tracking Total Tasks, Pending, Completed, Scheduled Today, and Active Reminders.
- **Live Search & Filter Bar**: Filter by status (All, Pending, Completed), priority (High, Medium, Low), or search by keyword.
- **Quick Status Toggle**: Mark tasks completed or pending with one click directly from cards.

---

## 🚀 Getting Started

### 1. Requirements
Ensure Python 3.10+ is installed. Install required packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Launch the Flask development server:
```bash
python tut1.py
# or
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Demo Credentials
- **Username**: `demo`
- **Password**: `password123`
*(Or click "Sign Up" to create your own private user account!)*

---

## 🧪 Running Unit Tests

Run the full automated test suite covering registration, user isolation, scheduling, reminders, and filters:
```bash
python -m pytest tests/test_app.py -v
```

---

## 📂 Project Structure

```
Flask/
├── app.py                  # Standard Flask entry point
├── tut1.py                 # Core application logic, routes, and models
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css       # Modern custom styling, variables, animations
│   └── js/
│       └── main.js         # Audio chime synthesizer, notifications, toggles
├── templates/
│   ├── base.html           # Base layout, navbar, notification bell, footer
│   ├── index.html          # Dashboard, statistics, add form, timeline & cards
│   ├── update.html         # Task and schedule editor form
│   ├── login.html          # Authentication login card
│   └── register.html       # User registration card
└── tests/
    └── test_app.py         # Automated pytest suite
```
