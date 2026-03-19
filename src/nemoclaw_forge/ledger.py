import datetime
import os
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    item = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, default="General")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    note = Column(String, nullable=True)

class LedgerManager:
    """Manages the database interactions for the Moonlight Ledger."""
    def __init__(self, db_path: str = "nemoclaw_ledger.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_expense(self, item: str, amount: float, category: str = "General", note: str = None):
        session = self.Session()
        new_expense = Expense(item=item, amount=amount, category=category, note=note)
        session.add(new_expense)
        session.commit()
        expense_id = new_expense.id
        session.close()
        return expense_id

    def get_summary(self, days: int = 30):
        session = self.Session()
        # Simple summary for now
        expenses = session.query(Expense).all()
        total = sum(e.amount for e in expenses)
        session.close()
        return {"total": total, "count": len(expenses)}

    def get_all(self):
        session = self.Session()
        expenses = session.query(Expense).order_by(Expense.timestamp.desc()).all()
        result = [
            {
                "id": e.id,
                "item": e.item,
                "amount": e.amount,
                "category": e.category,
                "timestamp": e.timestamp.isoformat()
            }
            for e in expenses
        ]
        session.close()
        return result
