from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from .ledger import LedgerManager

app = FastAPI(title="NemoClaw Moonlight Ledger API")
ledger = LedgerManager()

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

@app.get("/")
async def health():
    return {"status": "Moonlight Ledger API is active", "version": "0.1.0"}
