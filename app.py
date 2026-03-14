import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_carpool_key'

# ── Helpers ──────────────────────────────────────────────────

def get_db_connection():
    conn = sqlite3.connect('carpool.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    """Return the current user row or None."""
    if 'user_id' not in session:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

# ── Auth Routes ──────────────────────────────────────────────

@app.route('/register', methods=('GET', 'POST'))
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm  = request.form['confirm_password'].strip()

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            conn.close()
            flash('Username already taken. Choose another.', 'error')
            return redirect(url_for('register'))

        conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        conn.commit()
        conn.close()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ── Main Pages ───────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()

    conn = get_db_connection()

    query = "SELECT * FROM rides WHERE is_active = 1 AND date >= date('now')"
    params = []

    if source:
        query += " AND source LIKE ?"
        params.append(f"%{source}%")
    if destination:
        query += " AND destination LIKE ?"
        params.append(f"%{destination}%")

    query += " ORDER BY date ASC, time ASC"
    rides = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('index.html',
                           rides=rides,
                           source=source,
                           destination=destination)


@app.route('/post', methods=('GET', 'POST'))
@login_required
def post_ride():
    if request.method == 'POST':
        driver_name = request.form['driver_name']
        contact = request.form['contact']
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']
        time_val = request.form['time']
        seats_available = request.form['seats_available']
        cancel_password = request.form['cancel_password']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO rides (user_id, driver_name, source, destination, date, time,
                               seats_available, contact, cancel_password, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (session['user_id'], driver_name, source, destination, date, time_val,
              seats_available, contact, cancel_password))
        conn.commit()
        conn.close()

        flash('Ride posted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('post_ride.html')


@app.route('/ride/<int:id>')
@login_required
def ride_detail(id):
    conn = get_db_connection()
    ride = conn.execute('SELECT * FROM rides WHERE id = ?', (id,)).fetchone()

    if ride is None:
        conn.close()
        return "Ride not found", 404

    request_count = conn.execute(
        'SELECT COUNT(*) as cnt FROM requests WHERE ride_id = ?', (id,)
    ).fetchone()['cnt']

    # Check if the current logged-in user owns this ride
    is_owner = ('user_id' in session and session['user_id'] == ride['user_id'])

    # If owner, fetch requests directly
    requests_list = []
    if is_owner:
        requests_list = conn.execute(
            'SELECT * FROM requests WHERE ride_id = ? ORDER BY created_at ASC', (id,)
        ).fetchall()
        requests_list = [dict(r) for r in requests_list]

    # Check if the logged-in user (as a passenger) has an existing request on this ride
    my_request = None
    if 'user_id' in session and not is_owner:
        my_request = conn.execute(
            'SELECT * FROM requests WHERE ride_id = ? AND user_id = ?',
            (id, session['user_id'])
        ).fetchone()
        if my_request:
            my_request = dict(my_request)

    conn.close()

    return render_template('ride_detail.html',
                           ride=ride,
                           request_count=request_count,
                           is_owner=is_owner,
                           requests_list=requests_list,
                           my_request=my_request)


@app.route('/ride/<int:id>/view-requests', methods=('POST',))
def view_requests(id):
    password_input = request.form.get('cancel_password', '').strip()

    conn = get_db_connection()
    ride = conn.execute('SELECT cancel_password FROM rides WHERE id = ?', (id,)).fetchone()

    if ride and ride['cancel_password'] == password_input:
        reqs = conn.execute(
            'SELECT id, passenger_name, passenger_contact, status FROM requests WHERE ride_id = ?',
            (id,)
        ).fetchall()
        conn.close()
        return jsonify({'success': True, 'requests': [dict(r) for r in reqs]})

    conn.close()
    return jsonify({'success': False, 'message': 'Incorrect password'}), 403


@app.route('/ride/<int:id>/request', methods=('POST',))
def request_seat(id):
    passenger_name = request.form['passenger_name']
    passenger_contact = request.form['passenger_contact']

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO requests (ride_id, user_id, passenger_name, passenger_contact, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (id, session.get('user_id'), passenger_name, passenger_contact))
        conn.commit()
        flash('Seat requested successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('You have already requested a seat using this contact info.', 'error')
    finally:
        conn.close()

    return redirect(url_for('ride_detail', id=id))


@app.route('/ride/<int:ride_id>/accept-request/<int:req_id>', methods=('POST',))
@login_required
def accept_request(ride_id, req_id):
    conn = get_db_connection()
    ride = conn.execute('SELECT user_id FROM rides WHERE id = ?', (ride_id,)).fetchone()

    if not ride or ride['user_id'] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn.execute('UPDATE requests SET status = ? WHERE id = ? AND ride_id = ?',
                 ('accepted', req_id, ride_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': 'accepted'})


@app.route('/ride/<int:ride_id>/reject-request/<int:req_id>', methods=('POST',))
@login_required
def reject_request(ride_id, req_id):
    conn = get_db_connection()
    ride = conn.execute('SELECT user_id FROM rides WHERE id = ?', (ride_id,)).fetchone()

    if not ride or ride['user_id'] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn.execute('UPDATE requests SET status = ? WHERE id = ? AND ride_id = ?',
                 ('rejected', req_id, ride_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': 'rejected'})


@app.route('/ride/<int:id>/cancel', methods=('POST',))
def cancel_ride(id):
    password_input = request.form.get('cancel_password', '').strip()

    conn = get_db_connection()
    ride = conn.execute('SELECT cancel_password FROM rides WHERE id = ?', (id,)).fetchone()

    if ride and ride['cancel_password'] == password_input:
        conn.execute('UPDATE rides SET is_active = 0 WHERE id = ?', (id,))
        conn.commit()
        flash('Ride has been marked as Full/Cancelled.', 'success')
    else:
        flash('Incorrect password. Only the ride creator can cancel this ride.', 'error')

    conn.close()
    return redirect(url_for('ride_detail', id=id))

# ── Context Processor ────────────────────────────────────────

@app.context_processor
def inject_user():
    """Make current_user available to all templates."""
    return dict(current_user=get_current_user())

if __name__ == '__main__':
    app.run(debug=True)
