#!/bin/bash

# Initialize Finance App Database
# Usage: ./scripts/init_db.sh [--reset]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_DIR="$PROJECT_DIR/data"
DB_FILE="$DB_DIR/finance.db"
SCHEMA_FILE="$PROJECT_DIR/db/schema.sql"
SEED_FILE="$PROJECT_DIR/db/seed.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Finance App Database Initialization${NC}"
echo "========================================"

# Check for --reset flag
if [[ "$1" == "--reset" ]]; then
    echo -e "${YELLOW}Warning: This will delete all existing data!${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ -f "$DB_FILE" ]]; then
            rm "$DB_FILE"
            echo -e "${GREEN}Deleted existing database${NC}"
        fi
    else
        echo "Aborted."
        exit 0
    fi
fi

# Create data directory if it doesn't exist
if [[ ! -d "$DB_DIR" ]]; then
    mkdir -p "$DB_DIR"
    echo -e "${GREEN}Created data directory${NC}"
fi

# Check if database already exists
if [[ -f "$DB_FILE" ]]; then
    echo -e "${YELLOW}Database already exists at $DB_FILE${NC}"
    echo "Use --reset flag to recreate: ./scripts/init_db.sh --reset"

    # Still run schema (IF NOT EXISTS will skip existing tables)
    echo "Running schema (will skip existing tables)..."
    sqlite3 "$DB_FILE" < "$SCHEMA_FILE"
    echo -e "${GREEN}Schema check complete${NC}"

    # Check if categories need seeding
    CATEGORY_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM categories;")
    if [[ "$CATEGORY_COUNT" -eq 0 ]]; then
        echo "Seeding default categories..."
        sqlite3 "$DB_FILE" < "$SEED_FILE"
        echo -e "${GREEN}Seeded default categories${NC}"
    else
        echo "Categories already seeded ($CATEGORY_COUNT categories found)"
    fi
else
    # Create new database
    echo "Creating database at $DB_FILE..."

    # Run schema
    echo "Running schema..."
    sqlite3 "$DB_FILE" < "$SCHEMA_FILE"
    echo -e "${GREEN}Schema created${NC}"

    # Run seed
    echo "Seeding default data..."
    sqlite3 "$DB_FILE" < "$SEED_FILE"
    echo -e "${GREEN}Default data seeded${NC}"
fi

echo ""
echo -e "${GREEN}Database initialization complete!${NC}"
echo ""

# Show table info
echo "Tables created:"
sqlite3 "$DB_FILE" ".tables"
echo ""

echo "Category count: $(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM categories;")"
echo ""
echo "Run the app with: uvicorn app.main:app --reload"
