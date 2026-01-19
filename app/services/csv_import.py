import hashlib
import re
from datetime import datetime
from typing import Optional

import pandas as pd


# Known bank CSV formats for auto-detection
KNOWN_FORMATS = {
    "chase_credit": {
        "identifier_columns": {"Transaction Date", "Post Date", "Description", "Amount"},
        "mapping": {
            "date": "Transaction Date",
            "description": "Description",
            "amount": "Amount",
        },
        "date_format": "%m/%d/%Y",
        "amount_handling": "signed",
        "account_type": "credit_card",
        "institution": "Chase",
        "default_name": "Chase Credit Card",
    },
    "chase_checking": {
        "identifier_columns": {"Details", "Posting Date", "Description", "Amount", "Balance"},
        "mapping": {
            "date": "Posting Date",
            "description": "Description",
            "amount": "Amount",
        },
        "date_format": "%m/%d/%Y",
        "amount_handling": "signed",
        "account_type": "checking",
        "institution": "Chase",
        "default_name": "Chase Checking",
    },
    "bank_of_america": {
        "identifier_columns": {"Date", "Description", "Amount", "Running Bal."},
        "mapping": {
            "date": "Date",
            "description": "Description",
            "amount": "Amount",
        },
        "date_format": "%m/%d/%Y",
        "amount_handling": "signed",
        "account_type": "checking",
        "institution": "Bank of America",
        "default_name": "Bank of America Account",
    },
    "wells_fargo": {
        "identifier_columns": {"Date", "Amount", "Description"},
        "mapping": {
            "date": "Date",
            "description": "Description",
            "amount": "Amount",
        },
        "date_format": "%m/%d/%Y",
        "amount_handling": "signed",
        "account_type": "checking",
        "institution": "Wells Fargo",
        "default_name": "Wells Fargo Account",
    },
    "capital_one": {
        "identifier_columns": {"Transaction Date", "Posted Date", "Card No.", "Description", "Debit", "Credit"},
        "mapping": {
            "date": "Transaction Date",
            "description": "Description",
        },
        "date_format": "%Y-%m-%d",
        "amount_handling": "separate",
        "debit_column": "Debit",
        "credit_column": "Credit",
        "account_type": "credit_card",
        "institution": "Capital One",
        "default_name": "Capital One Card",
    },
    "mint_export": {
        "identifier_columns": {"Date", "Description", "Original Description", "Amount", "Transaction Type", "Category"},
        "mapping": {
            "date": "Date",
            "description": "Description",
            "original_description": "Original Description",
            "amount": "Amount",
            "category": "Category",
        },
        "date_format": "%m/%d/%Y",
        "amount_handling": "type_column",
        "type_column": "Transaction Type",
        "account_type": "checking",
        "institution": "Mint Import",
        "default_name": "Imported Account",
    },
}


def get_account_info_for_format(format_name: str) -> Optional[dict]:
    """Get suggested account info for a detected format."""
    if format_name not in KNOWN_FORMATS:
        return None

    fmt = KNOWN_FORMATS[format_name]
    return {
        "account_type": fmt.get("account_type", "checking"),
        "institution": fmt.get("institution", "Unknown"),
        "default_name": fmt.get("default_name", "Imported Account"),
    }


def detect_format(df: pd.DataFrame) -> Optional[str]:
    """Try to identify CSV format from column headers."""
    columns = set(df.columns.tolist())

    for format_name, format_info in KNOWN_FORMATS.items():
        required = format_info["identifier_columns"]
        if required.issubset(columns):
            return format_name

    return None


def infer_columns(df: pd.DataFrame) -> dict:
    """Guess which columns are date, amount, description for unknown formats."""
    suggestions = {"date": [], "amount": [], "description": []}

    for col in df.columns:
        sample = df[col].dropna().head(10).astype(str)

        # Check if date
        if _looks_like_date(sample):
            suggestions["date"].append(col)

        # Check if amount
        if _looks_like_amount(df[col].dropna().head(10)):
            suggestions["amount"].append(col)

        # Check if description
        if _looks_like_description(sample):
            suggestions["description"].append(col)

    return suggestions


def _looks_like_date(sample: pd.Series) -> bool:
    """Check if a column looks like dates."""
    date_patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY or M/D/YY
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{1,2}-\d{1,2}-\d{2,4}",  # MM-DD-YYYY
    ]

    matches = 0
    for val in sample:
        for pattern in date_patterns:
            if re.match(pattern, str(val).strip()):
                matches += 1
                break

    return matches >= len(sample) * 0.8


def _looks_like_amount(sample: pd.Series) -> bool:
    """Check if a column looks like monetary amounts."""
    try:
        # Try to parse as numbers
        cleaned = sample.astype(str).str.replace(r"[$,()]", "", regex=True)
        cleaned = cleaned.str.replace(r"^\s*-\s*$", "0", regex=True)
        pd.to_numeric(cleaned, errors="raise")

        # Check if values look like currency (has decimals, reasonable range)
        numeric = pd.to_numeric(cleaned, errors="coerce")
        has_decimals = any(numeric != numeric.astype(int))
        reasonable_range = numeric.abs().max() < 100000

        return has_decimals or reasonable_range
    except (ValueError, TypeError):
        return False


def _looks_like_description(sample: pd.Series) -> bool:
    """Check if a column looks like transaction descriptions."""
    avg_length = sample.str.len().mean()
    has_letters = sample.str.contains(r"[a-zA-Z]", regex=True).mean() > 0.8

    return avg_length > 10 and has_letters


def parse_csv(
    content: str,
    column_mapping: dict,
    date_format: str = "auto",
    amount_handling: str = "signed",
    debit_column: Optional[str] = None,
    credit_column: Optional[str] = None,
    type_column: Optional[str] = None,
    skip_rows: int = 0,
) -> list[dict]:
    """
    Parse CSV content into transaction dicts.

    Args:
        content: Raw CSV string
        column_mapping: {"date": "Date Column", "amount": "Amount Column", "description": "Desc Column"}
        date_format: strftime format or "auto"
        amount_handling: "signed", "separate", or "type_column"
        debit_column: Column name for debits (if amount_handling == "separate")
        credit_column: Column name for credits (if amount_handling == "separate")
        type_column: Column name for transaction type (if amount_handling == "type_column")
        skip_rows: Number of header rows to skip

    Returns:
        List of transaction dicts with keys: date, amount, description, original_description
    """
    from io import StringIO

    df = pd.read_csv(StringIO(content), skiprows=skip_rows)

    transactions = []

    for _, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row[column_mapping["date"]]).strip()
            date = _parse_date(date_str, date_format)
            if not date:
                continue

            # Parse amount
            if amount_handling == "signed":
                amount = _parse_amount(row[column_mapping["amount"]])
            elif amount_handling == "separate":
                debit = _parse_amount(row.get(debit_column, 0)) or 0
                credit = _parse_amount(row.get(credit_column, 0)) or 0
                amount = credit - debit  # Credits positive, debits negative
            elif amount_handling == "type_column":
                amount = _parse_amount(row[column_mapping["amount"]])
                txn_type = str(row.get(type_column, "")).lower()
                if "debit" in txn_type or "expense" in txn_type:
                    amount = -abs(amount)
                else:
                    amount = abs(amount)
            else:
                amount = _parse_amount(row[column_mapping["amount"]])

            if amount is None:
                continue

            # Parse description
            description = str(row[column_mapping["description"]]).strip()
            original_description = str(row.get(column_mapping.get("original_description", column_mapping["description"]), description)).strip()

            transactions.append({
                "date": date,
                "amount": amount,
                "description": description,
                "original_description": original_description,
                "merchant": _extract_merchant(description),
            })

        except (KeyError, ValueError) as e:
            # Skip invalid rows
            continue

    return transactions


def _parse_date(date_str: str, date_format: str = "auto") -> Optional[str]:
    """Parse date string to YYYY-MM-DD format."""
    if date_format == "auto":
        formats = [
            "%m/%d/%Y",
            "%m/%d/%y",
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]
    else:
        formats = [date_format]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _parse_amount(value) -> Optional[float]:
    """Parse amount string to float."""
    if pd.isna(value):
        return None

    try:
        # Handle string amounts with currency symbols
        cleaned = str(value).replace("$", "").replace(",", "").strip()

        # Handle parentheses as negative (accounting format)
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        # Handle empty or dash
        if cleaned in ("", "-", "--"):
            return 0.0

        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _extract_merchant(description: str) -> str:
    """Extract merchant name from transaction description."""
    # Remove common prefixes
    prefixes = ["POS ", "ACH ", "DEBIT ", "CREDIT ", "PURCHASE ", "CHECKCARD "]
    text = description.upper()
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]

    # Remove trailing numbers/codes
    text = re.sub(r"\s+\d{4,}.*$", "", text)
    text = re.sub(r"\s+#\d+.*$", "", text)
    text = re.sub(r"\s+\*+\d+.*$", "", text)

    # Clean up
    text = " ".join(text.split())

    return text.title()[:200]


def generate_import_hash(date: str, amount: float, description: str, account_id: int) -> str:
    """
    Generate unique hash for deduplication.

    Combines date + amount + normalized description + account to create
    a deterministic identifier for each transaction.
    """
    # Normalize description
    normalized = " ".join(description.lower().split())

    # Create deterministic string
    unique_string = f"{date}|{amount:.2f}|{normalized}|{account_id}"

    return hashlib.sha256(unique_string.encode()).hexdigest()
