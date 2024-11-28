from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, event, DateTime, Text
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from ..model_base import Base

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(25), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone('UTC', func.now()))
    updated_at = Column(DateTime, server_default=func.timezone('UTC', func.now()), onupdate=func.timezone('UTC', func.now()))
    
    reported_by_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reported_by = relationship('User', back_populates='support_issues')
    
