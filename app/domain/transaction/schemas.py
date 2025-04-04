from pydantic import BaseModel, constr
from datetime import datetime
from typing import Literal

class TransactionBase(BaseModel):
    user_id: int 
    status: str
    payu_order_id: str | None
    created_at: datetime

class TransactionCreate(TransactionBase):
    id: str

class Transaction(TransactionBase):
    id: str

class TransactionGet(BaseModel):
    status: str
    created_at: datetime
    id: str
    total_price: float

class TransactionItemBase(BaseModel):
    transaction_id: str
    article_id: int

class TransactionItemCreate(TransactionItemBase):
    paid_out: bool = False

class TransactionItemBase(TransactionItemBase):
    id: int
    paid_out: bool