from sqlalchemy.orm import Session
from sqlalchemy import case, func, or_
from passlib.context import CryptContext
from collections import Counter
from typing import Literal, Optional, List, Tuple
from . import models, schemas

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transaction(db: Session, transaction_id: str):
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()


def delete_transaction(db: Session, transaction_id: str):
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()

def create_transaction_item(db: Session, item: schemas.TransactionItemCreate):
    db_item = models.TransactionItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_transaction_items_by_transaction(db: Session, transaction_id: str):
    return db.query(models.TransactionItem).filter(models.TransactionItem.transaction_id == transaction_id).all()
