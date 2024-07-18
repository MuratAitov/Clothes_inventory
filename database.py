import sqlite3

def create_connection():
    conn = sqlite3.connect('inventory.db')
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS data_storage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        foreman TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        name TEXT NOT NULL,
        foreman TEXT NOT NULL,
        item TEXT NOT NULL,
        type TEXT NOT NULL,
        quantity TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

create_tables()
