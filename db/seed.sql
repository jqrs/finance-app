-- Finance App Default Data
-- Run with: sqlite3 data/finance.db < db/seed.sql

-- Default categories (only insert if table is empty)
INSERT OR IGNORE INTO categories (name, icon, color, is_expense, is_system) VALUES
    -- Income categories
    ('Salary', 'briefcase', '#22C55E', 0, 1),
    ('Freelance', 'laptop', '#10B981', 0, 1),
    ('Interest', 'percent', '#14B8A6', 0, 1),
    ('Refunds', 'rotate-ccw', '#06B6D4', 0, 1),
    ('Other Income', 'plus-circle', '#0EA5E9', 0, 1),
    -- Expense categories
    ('Housing', 'home', '#EF4444', 1, 1),
    ('Utilities', 'zap', '#F97316', 1, 1),
    ('Groceries', 'shopping-cart', '#F59E0B', 1, 1),
    ('Dining', 'utensils', '#EAB308', 1, 1),
    ('Transportation', 'car', '#84CC16', 1, 1),
    ('Entertainment', 'film', '#22C55E', 1, 1),
    ('Shopping', 'shopping-bag', '#14B8A6', 1, 1),
    ('Healthcare', 'heart', '#06B6D4', 1, 1),
    ('Subscriptions', 'repeat', '#0EA5E9', 1, 1),
    ('Travel', 'plane', '#3B82F6', 1, 1),
    ('Education', 'book', '#6366F1', 1, 1),
    ('Personal', 'user', '#8B5CF6', 1, 1),
    ('Fees', 'alert-circle', '#A855F7', 1, 1),
    ('Transfer', 'arrow-right-left', '#6B7280', 1, 1),
    ('Other', 'more-horizontal', '#9CA3AF', 1, 1);
