from fastapi import APIRouter

from app.api import accounts, categories, transactions, csv_import, predictions

api_router = APIRouter()

api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(csv_import.router, prefix="/import", tags=["import"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
