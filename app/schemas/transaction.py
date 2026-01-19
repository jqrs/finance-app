from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.account import AccountResponse
from app.schemas.category import CategoryResponse


class TransactionBase(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    date: date
    amount: float
    description: str
    merchant: Optional[str] = None
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    date: Optional[date] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    original_description: Optional[str] = None
    is_recurring: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionWithDetails(TransactionResponse):
    account: Optional[AccountResponse] = None
    category: Optional[CategoryResponse] = None


class TransactionSummary(BaseModel):
    total_income: float
    total_expenses: float
    net: float
    transaction_count: int
