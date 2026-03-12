import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'super_secret_carpool_key'

def get_db_connection():
    conn = sqlite3.connect('carpool.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()
    
    conn = get_db_connection()
    
    # 1. Fetch rides
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
    
    return render_template('index.html', 
                           rides=rides, 
                           source=source, 
                           destination=destination)

@app.route('/post', methods=('GET', 'POST'))
def post_ride():
    if request.method == 'POST':
        driver_name = request.form['driver_name']
        contact = request.form['contact']
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']
        time = request.form['time']
        seats_available = request.form['seats_available']
        cancel_password = request.form['cancel_password']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO rides (driver_name, source, destination, date, time, seats_available, contact, cancel_password, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (driver_name, source, destination, date, time, seats_available, contact, cancel_password))
        conn.commit()
        conn.close()
        
        flash('Ride posted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('post_ride.html')

@app.route('/ride/<int:id>')
def ride_detail(id):
    conn = get_db_connection()
    ride = conn.execute('SELECT * FROM rides WHERE id = ?', (id,)).fetchone()
    
    if ride is None:
        conn.close()
        return "Ride not found", 404

    request_count = conn.execute('SELECT COUNT(*) as cnt FROM requests WHERE ride_id = ?', (id,)).fetchone()['cnt']
    conn.close()
    
    return render_template('ride_detail.html', ride=ride, request_count=request_count)

@app.route('/ride/<int:id>/view-requests', methods=('POST',))
def view_requests(id):
    password_input = request.form.get('cancel_password', '').strip()
    
    conn = get_db_connection()
    ride = conn.execute('SELECT cancel_password FROM rides WHERE id = ?', (id,)).fetchone()
    
    if ride and ride['cancel_password'] == password_input:
        reqs = conn.execute('SELECT passenger_name, passenger_contact FROM requests WHERE ride_id = ?', (id,)).fetchall()
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
            INSERT INTO requests (ride_id, passenger_name, passenger_contact)
            VALUES (?, ?, ?)
        ''', (id, passenger_name, passenger_contact))
        conn.commit()
        flash('Seat requested successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('You have already requested a seat using this contact info.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('ride_detail', id=id))

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

if __name__ == '__main__':
    app.run(debug=False)
