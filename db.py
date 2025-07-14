import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            promo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_user(name, phone, promo):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, phone, promo) VALUES (?, ?, ?)", (name, phone, promo))
    conn.commit()
    conn.close()
