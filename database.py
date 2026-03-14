import sqlite3
import os
from werkzeug.security import generate_password_hash

def init_db():
    db_path = 'carpool.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed old database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Rides table
    cursor.execute('''
        CREATE TABLE rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            driver_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            seats_available INTEGER NOT NULL,
            contact TEXT NOT NULL,
            cancel_password TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Requests table
    cursor.execute('''
        CREATE TABLE requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL,
            user_id INTEGER,
            passenger_name TEXT NOT NULL,
            passenger_contact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ride_id) REFERENCES rides (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (ride_id, passenger_contact)
        )
    ''')

    # ── Sample Users ──
    users = [
        ('srikumar', 'pass'),
        ('rohit_reddy', 'pass'),
        ('karthik', 'pass'),
        ('sai_teja', 'pass'),
        ('sashank', 'pass'),
        ('sairam', 'pass'),
    ]
    for username, pwd in users:
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, generate_password_hash(pwd))
        )

    # ── Sample Rides ──
    rides = [
        (1, 'Sri Kumar',   'Hyderabad',  'Bangalore',   '2026-03-20', '06:00', 3, '9876543210', 'cancel123'),
        (2, 'Rohit Reddy', 'Hyderabad',  'Guntur',      '2026-03-20', '07:15', 2, '9988776655', 'cancel456'),
        (3, 'Karthik',     'Hyderabad',  'Vijayawada',  '2026-03-20', '05:30', 3, '9112233445', 'cancel789'),
        (4, 'Sai Teja',    'Hyderabad',  'Warangal',    '2026-03-21', '08:00', 4, '9001122334', 'cancel000'),
        (5, 'Sashank',     'Hyderabad',  'Nellore',     '2026-03-21', '06:45', 3, '9223344556', 'cancel111'),
        (6, 'Sairam',      'Rajahmundry','Mangalgiri',  '2026-03-22', '05:00', 2, '9334455667', 'cancel222'),
    ]
    for r in rides:
        cursor.execute('''
            INSERT INTO rides (user_id, driver_name, source, destination, date, time, seats_available, contact, cancel_password, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', r)

    conn.commit()
    conn.close()
    print("Database initialized with the new provided sample data!")
    print("Users: srikumar, rohit_reddy, karthik, sai_teja, sashank, sairam (all password: 'pass')")

if __name__ == '__main__':
    init_db()
