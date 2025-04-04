from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, event, DateTime, Text
from sqlalchemy.orm import relationship, Session, attributes
from sqlalchemy.sql import func
from ..model_base import Base
from ..article.service import add_purchased_article_event


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(255), ForeignKey("transactions.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    paid_out = Column(Boolean, nullable=False, default=False)

    transaction = relationship("Transaction", foreign_keys=[transaction_id], back_populates="items")
    article = relationship("Article", foreign_keys=[article_id], back_populates="transaction_items")



class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(255), primary_key=True, autoincrement=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    payu_order_id = Column(String(255), nullable=True)
    
    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")

    @property
    def total_price(self) -> float:
        price = 0
        for item in self.items:
            price += item.article.price
        return price

@event.listens_for(Session, "before_flush")
def track_status_changes(session, flush_context, instances):
    for obj in session.dirty:
        if isinstance(obj, Transaction):
            hist = attributes.get_history(obj, "status", passive=True)
            if hist.has_changes() and obj.status == "COMPLETED":
                setattr(obj, "_status_changed_to_completed", True)
    for obj in session.new:
        if isinstance(obj, Transaction) and obj.status == "COMPLETED":
            setattr(obj, "_status_changed_to_completed", True)

@event.listens_for(Session, "after_flush_postexec")
def after_status_completed(session, flush_context):
    for obj in session.identity_map.values():
        if isinstance(obj, Transaction) and getattr(obj, "_status_changed_to_completed", False):
            for item in obj.items:
                add_purchased_article_event(session, obj.user_id, item.article_id)
                # print(f"[EVENT] Purchase added: user {obj.user_id}, article {item.article_id}")

