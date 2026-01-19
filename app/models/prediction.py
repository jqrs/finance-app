from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class RecurringExpense(Base):
    """Detected recurring expenses (subscriptions, bills)."""
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    merchant = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    average_amount = Column(Float)
    frequency_days = Column(Integer)
    frequency_type = Column(String(20))  # weekly, monthly, yearly
    confidence = Column(Float)

    next_expected_date = Column(Date)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="recurring_group")


class SpendingForecast(Base):
    """Predicted spending by category."""
    __tablename__ = "spending_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    forecast_month = Column(Date)  # First day of predicted month
    predicted_amount = Column(Float)
    lower_bound = Column(Float)
    upper_bound = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


class CashflowForecast(Base):
    """Predicted account balances."""
    __tablename__ = "cashflow_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))

    forecast_date = Column(Date)
    predicted_balance = Column(Float)
    lower_bound = Column(Float)
    upper_bound = Column(Float)

    daily_predictions = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
