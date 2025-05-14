import sqlite3

def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    # Create expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create categories table for reference
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default categories if they don't exist
    default_categories = [
        ('Food', '🍔'),
        ('Transport', '🚗'),
        ('Shopping', '🛍️'),
        ('Bills', '💡'),
        ('Entertainment', '🎬'),
        ('Health', '🏥'),
        ('Travel', '✈️'),
        ('Education', '📚'),
        ('Gifts', '🎁'),
        ('Other', '📌')
    ]

    c.executemany('''
        INSERT OR IGNORE INTO categories (name, icon)
        VALUES (?, ?)
    ''', default_categories)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!") 