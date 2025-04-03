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
    paid_out: bool

class TransactionItemBase(BaseModel):
    transaction_id: str
    article_id: int

class TransactionItemCreate(TransactionItemBase):
    pass

class TransactionItemBase(TransactionItemBase):
    id: int