from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Negative for expenses
    description = Column(String(500), nullable=False)
    original_description = Column(String(500))

    # For deduplication
    import_hash = Column(String(64), unique=True, index=True)

    # Metadata
    merchant = Column(String(200))
    is_recurring = Column(Boolean, default=False)
    recurring_group_id = Column(Integer, ForeignKey("recurring_expenses.id"), nullable=True)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    recurring_group = relationship("RecurringExpense", back_populates="transactions")
