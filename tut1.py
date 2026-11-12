from datetime import datetime, date, timezone
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'taskflow-super-secret-key-2026-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------------------------------------------------------------
# Database Models
# -------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship: Each user has their own isolated todos
    todos = db.relationship('Todo', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Todo(db.Model):
    __tablename__ = 'todos'
    sno = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(1000), nullable=True, default='')
    category = db.Column(db.String(50), default='Work')
    priority = db.Column(db.String(20), default='Medium') # High, Medium, Low
    status = db.Column(db.String(20), default='Pending')   # Pending, In Progress, Completed
    
    # Scheduling fields
    schedule_date = db.Column(db.String(10), nullable=True) # YYYY-MM-DD
    start_time = db.Column(db.String(5), nullable=True)     # HH:MM
    end_time = db.Column(db.String(5), nullable=True)       # HH:MM
    
    # Reminder fields
    reminder_datetime = db.Column(db.String(16), nullable=True) # YYYY-MM-DDTHH:MM
    reminder_dismissed = db.Column(db.Boolean, default=False)
    
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'sno': self.sno,
            'title': self.title,
            'desc': self.desc,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'schedule_date': self.schedule_date,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'reminder_datetime': self.reminder_datetime,
            'reminder_dismissed': self.reminder_dismissed,
        }

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title} (User: {self.user_id})"

# -------------------------------------------------------------------------
# Helper Functions & Decorators
# -------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access your personal dashboard.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

# -------------------------------------------------------------------------
# Database Initialization & Sample Data
# -------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    # Seed default demo account if no users exist
    if not User.query.first():
        demo_user = User(username='demo', email='demo@taskflow.local')
        demo_user.set_password('password123')
        db.session.add(demo_user)
        db.session.commit()

        today_str = date.today().isoformat()
        sample_todos = [
            Todo(
                user_id=demo_user.id,
                title='Review Project Architecture & Specs',
                desc='Go through frontend wireframes, API contracts, and database schema diagrams.',
                category='Work',
                priority='High',
                status='Pending',
                schedule_date=today_str,
                start_time='09:30',
                end_time='11:00',
                reminder_datetime=f"{today_str}T09:15"
            ),
            Todo(
                user_id=demo_user.id,
                title='Team Daily Standup & Sprint Sync',
                desc='Share blockers, progress updates, and timeline commitments with the squad.',
                category='Work',
                priority='Medium',
                status='Pending',
                schedule_date=today_str,
                start_time='11:30',
                end_time='12:00',
                reminder_datetime=f"{today_str}T11:25"
            ),
            Todo(
                user_id=demo_user.id,
                title='Evening Cardio & Fitness Session',
                desc='30-minute steady-state run followed by core stretching.',
                category='Fitness',
                priority='Low',
                status='Pending',
                schedule_date=today_str,
                start_time='18:00',
                end_time='19:00',
                reminder_datetime=f"{today_str}T17:45"
            )
        ]
        db.session.add_all(sample_todos)
        db.session.commit()

# -------------------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please pick another one.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please log in.', 'danger')
            return render_template('register.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash('Account registered successfully! Welcome to TaskFlow.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------------------------------------------------
# Todo & Schedule Dashboard Routes
# -------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = get_current_user()

    # Legacy/Direct POST support on '/'
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        category = request.form.get('category', 'Work')
        priority = request.form.get('priority', 'Medium')
        schedule_date = request.form.get('schedule_date', '').strip() or None
        start_time = request.form.get('start_time', '').strip() or None
        end_time = request.form.get('end_time', '').strip() or None
        reminder_datetime = request.form.get('reminder_datetime', '').strip() or None

        if title:
            todo = Todo(
                user_id=user.id,
                title=title,
                desc=desc,
                category=category,
                priority=priority,
                schedule_date=schedule_date,
                start_time=start_time,
                end_time=end_time,
                reminder_datetime=reminder_datetime
            )
            db.session.add(todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('dashboard'))

    # Query Filters
    selected_status = request.args.get('status', 'All')
    selected_priority = request.args.get('priority', 'All')
    date_filter = request.args.get('date_filter', '')
    search_query = request.args.get('search', '').strip()
    active_view = request.args.get('view', 'cards') # 'cards' or 'schedule'

    query = Todo.query.filter_by(user_id=user.id)

    # Compute high-level user stats
    total_count = query.count()
    completed_count = Todo.query.filter_by(user_id=user.id, status='Completed').count()
    pending_count = total_count - completed_count
    
    today_iso = date.today().isoformat()
    scheduled_today = Todo.query.filter(
        Todo.user_id == user.id,
        Todo.schedule_date == today_iso
    ).count()

    reminders_active = Todo.query.filter(
        Todo.user_id == user.id,
        Todo.reminder_datetime.isnot(None),
        Todo.reminder_dismissed == False,
        Todo.status != 'Completed'
    ).count()

    # Apply search filter
    if search_query:
        query = query.filter(
            (Todo.title.ilike(f"%{search_query}%")) | (Todo.desc.ilike(f"%{search_query}%"))
        )

    # Apply status filter
    if selected_status in ['Pending', 'Completed', 'In Progress']:
        query = query.filter_by(status=selected_status)

    # Apply priority filter
    if selected_priority in ['High', 'Medium', 'Low']:
        query = query.filter_by(priority=selected_priority)

    # Apply date filter
    if date_filter == 'today':
        query = query.filter_by(schedule_date=today_iso)

    # Order by schedule date and start time ascending, then creation descending
    if active_view == 'schedule':
        atodos = query.order_by(
            Todo.schedule_date.asc().nullslast(),
            Todo.start_time.asc().nullslast(),
            Todo.sno.desc()
        ).all()
    else:
        atodos = query.order_by(
            Todo.status.asc(), # Pending first
            Todo.schedule_date.asc().nullslast(),
            Todo.start_time.asc().nullslast(),
            Todo.sno.desc()
        ).all()

    stats = {
        'total': total_count,
        'completed': completed_count,
        'pending': pending_count,
        'scheduled_today': scheduled_today,
        'reminders_active': reminders_active
    }

    return render_template(
        'index.html',
        atodos=atodos,
        stats=stats,
        selected_status=selected_status,
        selected_priority=selected_priority,
        date_filter=date_filter,
        search_query=search_query,
        active_view=active_view
    )


@app.route('/add', methods=['POST'])
@login_required
def add_todo():
    user = get_current_user()
    title = request.form.get('title', '').strip()
    desc = request.form.get('desc', '').strip()
    category = request.form.get('category', 'Work')
    priority = request.form.get('priority', 'Medium')
    schedule_date = request.form.get('schedule_date', '').strip() or None
    start_time = request.form.get('start_time', '').strip() or None
    end_time = request.form.get('end_time', '').strip() or None
    reminder_datetime = request.form.get('reminder_datetime', '').strip() or None

    if not title:
        flash('Title cannot be empty.', 'danger')
        return redirect(url_for('dashboard'))

    todo = Todo(
        user_id=user.id,
        title=title,
        desc=desc,
        category=category,
        priority=priority,
        schedule_date=schedule_date,
        start_time=start_time,
        end_time=end_time,
        reminder_datetime=reminder_datetime
    )
    db.session.add(todo)
    db.session.commit()
    flash('New scheduled task added successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/update/<int:sno>', methods=['GET', 'POST'])
@login_required
def update_todo(sno):
    user = get_current_user()
    todo = Todo.query.filter_by(sno=sno, user_id=user.id).first_or_404()

    if request.method == 'POST':
        todo.title = request.form.get('title', '').strip() or todo.title
        todo.desc = request.form.get('desc', '').strip()
        todo.category = request.form.get('category', todo.category)
        todo.priority = request.form.get('priority', todo.priority)
        todo.status = request.form.get('status', todo.status)
        
        todo.schedule_date = request.form.get('schedule_date', '').strip() or None
        todo.start_time = request.form.get('start_time', '').strip() or None
        todo.end_time = request.form.get('end_time', '').strip() or None

        if request.form.get('clear_reminder'):
            todo.reminder_datetime = None
            todo.reminder_dismissed = False
        else:
            new_reminder = request.form.get('reminder_datetime', '').strip() or None
            if new_reminder != todo.reminder_datetime:
                todo.reminder_datetime = new_reminder
                todo.reminder_dismissed = False

        db.session.commit()
        flash('Task and schedule updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('update.html', todo=todo)


@app.route('/delete/<int:sno>', methods=['GET', 'POST'])
@login_required
def delete_todo(sno):
    user = get_current_user()
    todo = Todo.query.filter_by(sno=sno, user_id=user.id).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    flash(f'Task "{todo.title}" deleted.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/toggle-status/<int:sno>', methods=['POST'])
@login_required
def toggle_status(sno):
    user = get_current_user()
    todo = Todo.query.filter_by(sno=sno, user_id=user.id).first_or_404()
    
    if todo.status == 'Completed':
        todo.status = 'Pending'
    else:
        todo.status = 'Completed'
        # Dismiss reminder when completed
        todo.reminder_dismissed = True

    db.session.commit()
    return jsonify({
        'success': True,
        'sno': todo.sno,
        'new_status': todo.status
    })


@app.route('/dismiss-reminder/<int:sno>', methods=['POST'])
@login_required
def dismiss_reminder(sno):
    user = get_current_user()
    todo = Todo.query.filter_by(sno=sno, user_id=user.id).first_or_404()
    todo.reminder_dismissed = True
    db.session.commit()
    return jsonify({'success': True, 'sno': todo.sno})


@app.route('/api/reminders', methods=['GET'])
@login_required
def get_reminders():
    user = get_current_user()
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M')

    active_todos = Todo.query.filter(
        Todo.user_id == user.id,
        Todo.reminder_datetime.isnot(None),
        Todo.reminder_dismissed == False,
        Todo.status != 'Completed'
    ).all()

    due_reminders = []
    for t in active_todos:
        if t.reminder_datetime and t.reminder_datetime <= now_str:
            due_reminders.append(t.to_dict())

    return jsonify({
        'active_count': len(active_todos),
        'due_count': len(due_reminders),
        'due_reminders': due_reminders
    })

# -------------------------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
