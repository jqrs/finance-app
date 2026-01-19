from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.config import settings
from app.api.router import api_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Personal finance tracking and forecasting app",
    version="0.1.0"
)

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Set up templates
templates_path = Path(__file__).parent.parent / "frontend" / "templates"
templates_path.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))

# Include API router
app.include_router(api_router, prefix="/api")


# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Transactions list page."""
    return templates.TemplateResponse("transactions.html", {"request": request})


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Accounts page."""
    return templates.TemplateResponse("accounts.html", {"request": request})


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """CSV import page."""
    return templates.TemplateResponse("import.html", {"request": request})


@app.get("/predictions", response_class=HTMLResponse)
async def predictions_page(request: Request):
    """ML predictions page."""
    return templates.TemplateResponse("predictions.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
