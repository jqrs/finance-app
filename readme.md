# Finance App

A personal finance tracking and forecasting application with ML-based predictions.

`## Features

- **Account Management**: Track multiple bank accounts, credit cards, and cash
- **Transaction Tracking**: View, filter, and categorize transactions
- **CSV Import**: Import transactions from bank exports (Chase, Bank of America, Wells Fargo, etc.)
- **Spending Analysis**: Visualize spending by category with charts
- **ML Forecasting** (Coming Soon):
  - Spending predictions by category
  - Cash flow forecasting
  - Recurring expense detection

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables and seeds default categories)
./scripts/init_db.sh

# Run the app
uvicorn app.main:app --reload

# Open in browser
open http://localhost:8000
```

## Project Structure

```
finance-app/
├── app/
│   ├── main.py          # FastAPI application
│   ├── config.py        # Settings
│   ├── database.py      # SQLite connection
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── api/             # REST API endpoints
│   ├── services/        # Business logic
│   └── ml/              # ML components (coming soon)
├── db/
│   ├── schema.sql       # Table definitions
│   └── seed.sql         # Default category data
├── scripts/
│   └── init_db.sh       # Database initialization script
├── frontend/
│   ├── templates/       # Jinja2 HTML templates
│   └── static/          # CSS, JS files
├── data/                # SQLite database
└── requirements.txt
```

## API Endpoints

### Accounts
- `GET /api/accounts/` - List all accounts
- `POST /api/accounts/` - Create account
- `GET /api/accounts/{id}` - Get account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Transactions
- `GET /api/transactions/` - List transactions (with filters)
- `POST /api/transactions/` - Create transaction
- `GET /api/transactions/{id}` - Get transaction
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction
- `PATCH /api/transactions/{id}/category` - Update category
- `GET /api/transactions/summary` - Get spending summary

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create custom category
- `GET /api/categories/spending` - Get spending by category

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Jinja2 templates, HTMX, Alpine.js, Tailwind CSS, Chart.js
- **ML**: scikit-learn, statsmodels (coming soon)

## Database

The database schema and seed data are managed via raw SQL files:

```bash
# Initialize database (first time setup)
./scripts/init_db.sh

# Reset database (deletes all data)
./scripts/init_db.sh --reset

# Manual SQL commands
sqlite3 data/finance.db "SELECT * FROM categories;"
```

Schema is defined in [db/schema.sql](db/schema.sql), default categories in [db/seed.sql](db/seed.sql).

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# View API docs
open http://localhost:8000/docs
```
