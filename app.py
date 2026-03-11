import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
import datetime

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
    
    # 2. Compute Stats
    # Active rides
    active_count = len(rides) if source or destination else conn.execute("SELECT COUNT(*) FROM rides WHERE is_active = 1 AND date >= date('now')").fetchone()[0]
    
    # Unique cities (combining source logic)
    # We will just fetch all active sources/destinations to be accurate for stats regardless of search
    all_active_rides = conn.execute("SELECT source, destination, seats_available FROM rides WHERE is_active = 1 AND date >= date('now')").fetchall()
    cities = set()
    total_seats = 0
    for r in all_active_rides:
        cities.add(r['source'].strip().title())
        cities.add(r['destination'].strip().title())
        total_seats += r['seats_available']
        
    cities_count = len(cities)

    conn.close()
    
    return render_template('index.html', 
                           rides=rides, 
                           source=source, 
                           destination=destination,
                           stats={'active_rides': active_count, 'cities': cities_count, 'seats': total_seats})

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

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO rides (driver_name, source, destination, date, time, seats_available, contact, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (driver_name, source, destination, date, time, seats_available, contact))
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

    requests = conn.execute('SELECT * FROM requests WHERE ride_id = ?', (id,)).fetchall()
    conn.close()
    
    return render_template('ride_detail.html', ride=ride, requests=requests)

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
    driver_contact_input = request.form.get('driver_contact', '').strip()
    
    conn = get_db_connection()
    ride = conn.execute('SELECT contact FROM rides WHERE id = ?', (id,)).fetchone()
    
    if ride and ride['contact'] == driver_contact_input:
        conn.execute('UPDATE rides SET is_active = 0 WHERE id = ?', (id,))
        conn.commit()
        flash('Ride has been marked as Full/Cancelled.', 'success')
    else:
        flash('Incorrect driver contact. You cannot cancel this ride.', 'error')
        
    conn.close()
    return redirect(url_for('ride_detail', id=id))

if __name__ == '__main__':
    app.run(debug=True)
