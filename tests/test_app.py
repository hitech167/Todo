import pytest
from tut1 import app, db, User, Todo

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_registration_and_login(client):
    # Register Alice
    resp = client.post('/register', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Account registered successfully' in resp.data

    # Logout
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b'logged out' in resp.data

    # Login
    resp = client.post('/login', data={
        'username': 'alice',
        'password': 'password123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'alice' in resp.data

def test_user_todo_isolation(client):
    # Register Alice & Bob
    client.post('/register', data={
        'username': 'alice',
        'email': 'alice@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    # Alice adds a todo
    client.post('/add', data={
        'title': 'Alice Secret Task',
        'desc': 'Only Alice can see this',
        'category': 'Work',
        'priority': 'High',
        'schedule_date': '2026-11-20',
        'start_time': '10:00',
        'end_time': '11:00',
        'reminder_datetime': '2026-11-20T09:45'
    }, follow_redirects=True)

    # Bob logs in
    client.get('/logout')
    client.post('/register', data={
        'username': 'bob',
        'email': 'bob@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    # Check dashboard for Bob: Alice's task should NOT be visible!
    dash_bob = client.get('/', follow_redirects=True)
    assert b'Alice Secret Task' not in dash_bob.data

    # Bob creates his own task
    client.post('/add', data={
        'title': 'Bob Solo Project',
        'desc': 'Work on backend design',
        'category': 'Study',
        'priority': 'Medium',
        'schedule_date': '2026-11-21',
        'start_time': '14:00',
        'end_time': '16:00',
        'reminder_datetime': '2026-11-21T13:30'
    }, follow_redirects=True)

    dash_bob = client.get('/')
    assert b'Bob Solo Project' in dash_bob.data

    # Bob cannot update or delete Alice's task (sno 1)
    with app.app_context():
        alice_task = Todo.query.filter_by(title='Alice Secret Task').first()
        alice_sno = alice_task.sno

    # Bob tries to access or update Alice's task
    update_resp = client.get(f'/update/{alice_sno}')
    assert update_resp.status_code == 404

    delete_resp = client.post(f'/delete/{alice_sno}')
    assert delete_resp.status_code == 404

def test_schedule_allocation_and_reminder(client):
    # Register & Login
    client.post('/register', data={
        'username': 'scheduler_user',
        'email': 'sched@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    # Add task with schedule and reminder
    client.post('/add', data={
        'title': 'Sprint Review Meeting',
        'desc': 'Present demo to stakeholders',
        'category': 'Work',
        'priority': 'High',
        'schedule_date': '2026-11-25',
        'start_time': '14:00',
        'end_time': '15:30',
        'reminder_datetime': '2026-11-25T13:45'
    }, follow_redirects=True)

    with app.app_context():
        task = Todo.query.filter_by(title='Sprint Review Meeting').first()
        assert task is not None
        assert task.schedule_date == '2026-11-25'
        assert task.start_time == '14:00'
        assert task.end_time == '15:30'
        assert task.reminder_datetime == '2026-11-25T13:45'
        assert task.reminder_dismissed is False

    # Check Schedule Timeline view
    timeline_resp = client.get('/?view=schedule')
    assert b'Sprint Review Meeting' in timeline_resp.data
    assert b'14:00' in timeline_resp.data
    assert b'15:30' in timeline_resp.data

    # Test Reminders API
    reminders_resp = client.get('/api/reminders')
    assert reminders_resp.status_code == 200
    json_data = reminders_resp.get_json()
    assert json_data['active_count'] == 1

    # Test Toggle Status
    toggle_resp = client.post(f'/toggle-status/{task.sno}')
    assert toggle_resp.status_code == 200
    assert toggle_resp.get_json()['new_status'] == 'Completed'

    # Once completed, reminder is dismissed
    with app.app_context():
        updated_task = db.session.get(Todo, task.sno)
        assert updated_task.status == 'Completed'
        assert updated_task.reminder_dismissed is True

    # Test Update Task
    client.post(f'/update/{task.sno}', data={
        'title': 'Sprint Review & Retrospective',
        'desc': 'Updated agenda',
        'category': 'Work',
        'priority': 'High',
        'status': 'In Progress',
        'schedule_date': '2026-11-26',
        'start_time': '15:00',
        'end_time': '16:30'
    }, follow_redirects=True)

    with app.app_context():
        updated_task = db.session.get(Todo, task.sno)
        assert updated_task.title == 'Sprint Review & Retrospective'
        assert updated_task.schedule_date == '2026-11-26'
        assert updated_task.start_time == '15:00'
        assert updated_task.end_time == '16:30'


def test_filters_and_search(client):
    # Register user
    client.post('/register', data={
        'username': 'filter_user',
        'email': 'filter@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    # Add multiple tasks
    client.post('/add', data={
        'title': 'Alpha Urgent Bug Fix',
        'desc': 'Fix critical production crash',
        'category': 'Urgent',
        'priority': 'High',
        'schedule_date': '2026-11-15',
        'start_time': '09:00',
        'end_time': '10:00'
    })
    client.post('/add', data={
        'title': 'Beta Documentation Writeup',
        'desc': 'Write user manuals',
        'category': 'Study',
        'priority': 'Low',
        'schedule_date': '2026-11-16',
        'start_time': '11:00',
        'end_time': '12:00'
    })

    # Search for "Bug Fix"
    search_resp = client.get('/?search=Bug+Fix')
    assert b'Alpha Urgent Bug Fix' in search_resp.data
    assert b'Beta Documentation Writeup' not in search_resp.data

    # Filter by Priority: High
    prio_resp = client.get('/?priority=High')
    assert b'Alpha Urgent Bug Fix' in prio_resp.data
    assert b'Beta Documentation Writeup' not in prio_resp.data

def test_reminder_dismissal(client):
    client.post('/register', data={
        'username': 'reminder_user',
        'email': 'rem@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    client.post('/add', data={
        'title': 'Wake Up Call',
        'desc': 'Early morning start',
        'category': 'Personal',
        'priority': 'High',
        'schedule_date': '2026-11-12',
        'start_time': '07:00',
        'end_time': '08:00',
        'reminder_datetime': '2026-11-12T06:50'
    })

    with app.app_context():
        task = Todo.query.filter_by(title='Wake Up Call').first()
        sno = task.sno

    # Dismiss reminder
    dismiss_resp = client.post(f'/dismiss-reminder/{sno}')
    assert dismiss_resp.status_code == 200
    assert dismiss_resp.get_json()['success'] is True

    with app.app_context():
        task = db.session.get(Todo, sno)
        assert task.reminder_dismissed is True
