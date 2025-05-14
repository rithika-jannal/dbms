# Personal Finance Tracker

A Flask-based web application for tracking personal expenses and managing finances.

## Features

- Track daily expenses with categories
- View expense history and statistics
- Generate monthly and category-wise reports
- Modern and responsive UI
- Data validation and error handling

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
.
├── app.py              # Main Flask application
├── finance.db          # SQLite database
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS)
│   └── style.css
└── templates/         # HTML templates
    ├── base.html
    ├── index.html
    ├── add_expense.html
    ├── expenses.html
    └── reports.html
```

## Usage

1. Add Expenses:
   - Click "Add Expense" in the navigation bar
   - Fill in the expense details (category, amount, date, description)
   - Click "Add Expense" to save

2. View Expenses:
   - Click "Expenses" to see all expenses
   - Expenses are sorted by date
   - Use the delete button to remove expenses

3. View Reports:
   - Click "Reports" to see expense statistics
   - View category-wise and monthly summaries
   - Track total expenses and trends

## Contributing

Feel free to submit issues and enhancement requests!