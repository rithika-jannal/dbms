from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
from contextlib import contextmanager
from werkzeug.exceptions import HTTPException
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure file handler
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

# Database configuration
DATABASE = os.environ.get('DATABASE_URL', 'finance.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    if not os.path.exists(DATABASE):
        try:
            with get_db_connection() as conn:
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

                # Create categories table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        icon TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Insert default categories
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
                logger.info("Database initialized successfully!")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

def validate_expense(category, amount, date):
    """Validate expense input data"""
    errors = []
    
    # Validate category
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM categories WHERE name = ?", (category,))
        if not c.fetchone():
            errors.append("Invalid category selected")
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            errors.append("Amount must be greater than 0")
        if amount > 1000000:  # Reasonable maximum amount
            errors.append("Amount seems too large")
    except ValueError:
        errors.append("Invalid amount format")
    
    # Validate date
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        if date_obj > datetime.now():
            errors.append("Date cannot be in the future")
    except ValueError:
        errors.append("Invalid date format")
    
    return errors

@app.errorhandler(Exception)
def handle_error(error):
    """Handle all errors"""
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    
    logger.error(f"Error {code}: {str(error)}")
    return render_template('error.html', error=error), code

@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Get recent expenses
            c.execute("""
                SELECT e.*, c.icon 
                FROM expenses e
                LEFT JOIN categories c ON e.category = c.name
                ORDER BY e.date DESC 
                LIMIT 5
            """)
            recent_expenses = c.fetchall()
            
            # Get total expenses
            c.execute("SELECT SUM(amount) as total FROM expenses")
            total_expenses = c.fetchone()['total'] or 0
            
            # Get expense count
            c.execute("SELECT COUNT(*) as count FROM expenses")
            expense_count = c.fetchone()['count']
            
            # Get last added expense date
            c.execute("""
                SELECT date 
                FROM expenses 
                ORDER BY date DESC 
                LIMIT 1
            """)
            last_added = c.fetchone()
            
            return render_template('index.html',
                                expenses=recent_expenses,
                                total_expenses=total_expenses,
                                expense_count=expense_count,
                                last_added=last_added['date'] if last_added else None)
    except sqlite3.Error as e:
        logger.error(f"Database error in index: {str(e)}")
        flash(f"Database error: {str(e)}", "error")
        return render_template('index.html', expenses=[], total_expenses=0, expense_count=0, last_added=None)

@app.route('/expenses')
def expenses():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Get all expenses with category icons
            c.execute("""
                SELECT e.*, c.icon 
                FROM expenses e
                LEFT JOIN categories c ON e.category = c.name
                ORDER BY e.date DESC
            """)
            expenses = c.fetchall()
            
            # Get total expenses
            c.execute("SELECT SUM(amount) as total FROM expenses")
            total_expenses = c.fetchone()['total'] or 0
            
            return render_template('expenses.html',
                                expenses=expenses,
                                total_expenses=total_expenses)
    except sqlite3.Error as e:
        logger.error(f"Database error in expenses: {str(e)}")
        flash(f"Database error: {str(e)}", "error")
        return render_template('expenses.html', expenses=[], total_expenses=0)

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        description = request.form.get('description', '').strip()

        # Validate input
        errors = validate_expense(category, amount, date)
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for('add_expense'))

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO expenses (category, amount, date, description)
                    VALUES (?, ?, ?, ?)
                """, (category, amount, date, description))
                conn.commit()
                flash('Expense added successfully!', 'success')
                return redirect(url_for('expenses'))
        except sqlite3.Error as e:
            logger.error(f"Database error in add_expense: {str(e)}")
            flash(f"Error adding expense: {str(e)}", "error")
            return redirect(url_for('add_expense'))
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT name, icon FROM categories ORDER BY name")
            categories = c.fetchall()
            return render_template('add_expense.html', categories=categories)
    except sqlite3.Error as e:
        logger.error(f"Database error in add_expense form: {str(e)}")
        flash(f"Error loading categories: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/reports')
def reports():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Get expenses by category
            c.execute("""
                SELECT 
                    e.category,
                    c.icon,
                    SUM(e.amount) as total,
                    COUNT(*) as count
                FROM expenses e
                LEFT JOIN categories c ON e.category = c.name
                GROUP BY e.category
                ORDER BY total DESC
            """)
            category_totals = c.fetchall()
            
            # Get monthly totals
            c.execute("""
                SELECT 
                    strftime('%Y-%m', date) as month,
                    SUM(amount) as total,
                    COUNT(*) as count
                FROM expenses
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """)
            monthly_totals = c.fetchall()
            
            # Get total expenses
            c.execute("SELECT SUM(amount) as total FROM expenses")
            total_expenses = c.fetchone()['total'] or 0
            
            return render_template('reports.html',
                                category_totals=category_totals,
                                monthly_totals=monthly_totals,
                                total_expenses=total_expenses)
    except sqlite3.Error as e:
        logger.error(f"Database error in reports: {str(e)}")
        flash(f"Error loading reports: {str(e)}", "error")
        return render_template('reports.html', 
                             category_totals=[], 
                             monthly_totals=[], 
                             total_expenses=0)

@app.route('/delete-expense/<int:id>', methods=['POST'])
def delete_expense(id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM expenses WHERE id = ?", (id,))
            conn.commit()
            flash('Expense deleted successfully!', 'success')
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_expense: {str(e)}")
        flash(f"Error deleting expense: {str(e)}", "error")
    
    return redirect(url_for('expenses'))

@app.route('/api/expenses')
def api_expenses():
    """API endpoint to get expenses"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT e.*, c.icon 
                FROM expenses e
                LEFT JOIN categories c ON e.category = c.name
                ORDER BY e.date DESC
            """)
            expenses = c.fetchall()
            return jsonify([dict(expense) for expense in expenses])
    except sqlite3.Error as e:
        logger.error(f"Database error in api_expenses: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/daily-track')
def daily_track():
    return render_template('daily_track.html')

@app.route('/montly-track')
def montly_track():
    return render_template('montly_track.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')

