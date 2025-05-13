from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row  # This enables name-based access to columns
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses = c.fetchall()
    conn.close()
    
    # Get current year for the footer
    current_year = datetime.now().year
    
    return render_template('index.html', 
                          expenses=expenses, 
                          now={'year': current_year})

@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form['category']
    amount = request.form['amount']
    date = request.form['date']

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)",
              (category, amount, date))
    conn.commit()
    conn.close()

    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)

