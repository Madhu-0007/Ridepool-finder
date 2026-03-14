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

    # Rides table — now linked to a user
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

    # Requests table — now has status and user_id
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

    conn.commit()
    conn.close()
    print("Database initialized successfully with the new schema.")

if __name__ == '__main__':
    init_db()
