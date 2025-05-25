from fastapi import APIRouter

# Inisialisasi router utama
router = APIRouter()

# Import sub-routers setelah inisialisasi router utama
from .routes.balance import router as balance_router
from .routes.stock import router as stock_router 
from .routes.transactions import router as transactions_router

# Include sub-routers
router.include_router(balance_router, prefix="/balance", tags=["Balance"])
router.include_router(stock_router, prefix="/stock", tags=["Stock"])
router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}