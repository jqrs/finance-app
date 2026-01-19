from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategorySpending

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    is_expense: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all categories."""
    query = db.query(Category)
    if is_expense is not None:
        query = query.filter(Category.is_expense == is_expense)
    return query.order_by(Category.name).all()


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new custom category."""
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    db_category = Category(**category.model_dump(), is_system=False)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/spending", response_model=List[CategorySpending])
def get_spending_by_category(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get aggregated spending by category."""
    from datetime import datetime

    query = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        Category.color,
        func.sum(Transaction.amount).label("total"),
        func.count(Transaction.id).label("transaction_count")
    ).join(Transaction, Transaction.category_id == Category.id)

    if start_date:
        query = query.filter(Transaction.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Transaction.date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    results = query.group_by(Category.id).all()

    return [
        CategorySpending(
            category_id=r.category_id,
            category_name=r.category_name,
            color=r.color or "#6B7280",
            total=abs(r.total) if r.total else 0,
            transaction_count=r.transaction_count
        )
        for r in results
    ]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    """Update a category."""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category (only non-system categories)."""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if db_category.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system category")

    db.delete(db_category)
    db.commit()
