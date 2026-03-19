from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from .ledger import LedgerManager

app = FastAPI(title="NemoClaw Moonlight Ledger API")
ledger = LedgerManager()

# Define paths
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class ExpenseCreate(BaseModel):
    item: str
    amount: float
    category: Optional[str] = "General"
    note: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: int
    item: str
    amount: float
    category: str
    timestamp: str

@app.post("/expenses", response_model=dict)
async def add_expense(expense: ExpenseCreate):
    expense_id = ledger.add_expense(
        item=expense.item,
        amount=expense.amount,
        category=expense.category,
        note=expense.note
    )
    return {"status": "success", "id": expense_id}

@app.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses():
    return ledger.get_all()

@app.get("/summary")
async def get_summary():
    return ledger.get_summary()

# Root endpoint serves the Moonlight UI
@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# Mount static files (if we add CSS/JS files later)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
