-- Finance App Database Schema
-- Run with: sqlite3 data/finance.db < db/schema.sql

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('checking', 'savings', 'credit_card', 'investment', 'cash')),
    institution VARCHAR(100),
    last_four VARCHAR(4),
    current_balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES categories(id),
    icon VARCHAR(50),
    color VARCHAR(7),
    is_expense BOOLEAN DEFAULT 1,
    is_system BOOLEAN DEFAULT 0
);

-- Recurring expenses table (must be created before transactions due to FK)
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    average_amount REAL,
    frequency_days INTEGER,
    frequency_type VARCHAR(20),
    confidence REAL,
    next_expected_date DATE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id),
    date DATE NOT NULL,
    amount REAL NOT NULL,
    description VARCHAR(500) NOT NULL,
    original_description VARCHAR(500),
    import_hash VARCHAR(64) UNIQUE,
    merchant VARCHAR(200),
    is_recurring BOOLEAN DEFAULT 0,
    recurring_group_id INTEGER REFERENCES recurring_expenses(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CSV mappings table
CREATE TABLE IF NOT EXISTS csv_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    account_id INTEGER REFERENCES accounts(id),
    column_mapping JSON NOT NULL,
    date_format VARCHAR(50) DEFAULT '%Y-%m-%d',
    amount_handling VARCHAR(20) DEFAULT 'signed',
    debit_column VARCHAR(100),
    credit_column VARCHAR(100),
    type_column VARCHAR(100),
    skip_rows INTEGER DEFAULT 0
);

-- Spending forecasts table
CREATE TABLE IF NOT EXISTS spending_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id),
    forecast_month DATE,
    predicted_amount REAL,
    lower_bound REAL,
    upper_bound REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cashflow forecasts table
CREATE TABLE IF NOT EXISTS cashflow_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(id),
    forecast_date DATE,
    predicted_balance REAL,
    lower_bound REAL,
    upper_bound REAL,
    daily_predictions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_import_hash ON transactions(import_hash);
