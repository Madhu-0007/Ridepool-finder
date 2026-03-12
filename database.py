import sqlite3
import os

def init_db():
    db_path = 'carpool.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed old database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create new rides table
    cursor.execute('''
        CREATE TABLE rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            seats_available INTEGER NOT NULL,
            contact TEXT NOT NULL,
            cancel_password TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create new requests table
    cursor.execute('''
        CREATE TABLE requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL,
            passenger_name TEXT NOT NULL,
            passenger_contact TEXT NOT NULL,
            FOREIGN KEY (ride_id) REFERENCES rides (id),
            UNIQUE (ride_id, passenger_contact)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully with the new schema.")

if __name__ == '__main__':
    init_db()
