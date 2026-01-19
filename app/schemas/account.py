from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.account import AccountType


class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    institution: Optional[str] = None
    last_four: Optional[str] = None
    current_balance: float = 0.0


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    institution: Optional[str] = None
    last_four: Optional[str] = None
    current_balance: Optional[float] = None


class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
