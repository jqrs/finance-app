from typing import Optional

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_expense: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_expense: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    is_system: bool

    class Config:
        from_attributes = True


class CategorySpending(BaseModel):
    category_id: int
    category_name: str
    color: str
    total: float
    transaction_count: int
