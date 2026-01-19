from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.ml.recurring_detector import detect_recurring_expenses
from app.ml.spending_forecast import forecast_spending
from app.ml.cashflow_forecast import forecast_cashflow

router = APIRouter()


@router.get("/recurring")
async def get_recurring_expenses(
    min_occurrences: int = Query(3, ge=2, le=10),
    db: Session = Depends(get_db),
):
    """
    Detect recurring expenses from transaction history.
    Returns subscriptions and bills with confidence scores.
    """
    # Get all transactions
    transactions = db.query(Transaction).all()

    if len(transactions) < 10:
        return {
            "message": "Not enough transactions for recurring detection",
            "required": 10,
            "current": len(transactions),
            "recurring": [],
        }

    # Convert to dicts
    txn_data = [
        {
            "date": t.date.isoformat(),
            "amount": t.amount,
            "description": t.description,
        }
        for t in transactions
    ]

    recurring = detect_recurring_expenses(txn_data, min_occurrences)

    return {
        "total_transactions": len(transactions),
        "recurring_count": len(recurring),
        "recurring": recurring,
    }


@router.get("/spending-forecast")
async def get_spending_forecast(
    category_id: Optional[int] = None,
    months_ahead: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """
    Forecast future spending by category.
    Requires at least 3 months of categorized transaction data.
    """
    # Get categorized transactions
    query = db.query(Transaction).filter(Transaction.category_id.isnot(None))

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    transactions = query.all()

    if len(transactions) < 20:
        return {
            "message": "Not enough categorized transactions for forecasting",
            "required": 20,
            "current": len(transactions),
            "predictions": {},
        }

    # Convert to dicts
    txn_data = [
        {
            "date": t.date.isoformat(),
            "amount": t.amount,
            "category_id": t.category_id,
        }
        for t in transactions
    ]

    result = forecast_spending(txn_data, category_id, months_ahead)

    # Add category names to response
    categories = {c.id: c.name for c in db.query(Category).all()}

    predictions_with_names = {}
    for cat_id, preds in result["predictions"].items():
        predictions_with_names[cat_id] = {
            "category_name": categories.get(cat_id, "Unknown"),
            "forecasts": preds,
        }

    return {
        "training": result["training"],
        "months_ahead": months_ahead,
        "predictions": predictions_with_names,
    }


@router.get("/cashflow")
async def get_cashflow_forecast(
    account_id: Optional[int] = None,
    days_ahead: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """
    Forecast future account balances.
    Requires at least 30 days of transaction history.
    """
    # Get account and current balance
    if account_id:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        current_balance = account.current_balance
        transactions = db.query(Transaction).filter(
            Transaction.account_id == account_id
        ).all()
    else:
        # Use all accounts
        accounts = db.query(Account).all()
        current_balance = sum(a.current_balance for a in accounts)
        transactions = db.query(Transaction).all()

    if len(transactions) < 30:
        return {
            "message": "Not enough transactions for cashflow forecasting",
            "required": 30,
            "current": len(transactions),
            "predictions": [],
        }

    # Convert to dicts
    txn_data = [
        {
            "date": t.date.isoformat(),
            "amount": t.amount,
        }
        for t in transactions
    ]

    # Get recurring expenses for better prediction
    recurring = detect_recurring_expenses([
        {"date": t.date.isoformat(), "amount": t.amount, "description": t.description}
        for t in transactions
    ])

    result = forecast_cashflow(
        txn_data,
        current_balance,
        recurring,
        days_ahead,
    )

    return {
        "current_balance": current_balance,
        "training": result["training"],
        "days_ahead": days_ahead,
        "predictions": result["predictions"],
    }


@router.get("/summary")
async def get_predictions_summary(db: Session = Depends(get_db)):
    """
    Get a summary of available predictions and data requirements.
    """
    total_transactions = db.query(Transaction).count()
    categorized_transactions = db.query(Transaction).filter(
        Transaction.category_id.isnot(None)
    ).count()

    # Check date range
    from sqlalchemy import func
    date_range = db.query(
        func.min(Transaction.date),
        func.max(Transaction.date),
    ).first()

    if date_range[0] and date_range[1]:
        days_of_data = (date_range[1] - date_range[0]).days
    else:
        days_of_data = 0

    return {
        "data_summary": {
            "total_transactions": total_transactions,
            "categorized_transactions": categorized_transactions,
            "days_of_data": days_of_data,
            "date_range": {
                "start": date_range[0].isoformat() if date_range[0] else None,
                "end": date_range[1].isoformat() if date_range[1] else None,
            },
        },
        "feature_availability": {
            "recurring_detection": {
                "available": total_transactions >= 10,
                "requirement": "10+ transactions",
            },
            "spending_forecast": {
                "available": categorized_transactions >= 20 and days_of_data >= 60,
                "requirement": "20+ categorized transactions, 60+ days of data",
            },
            "cashflow_forecast": {
                "available": total_transactions >= 30 and days_of_data >= 30,
                "requirement": "30+ transactions, 30+ days of data",
            },
        },
    }
