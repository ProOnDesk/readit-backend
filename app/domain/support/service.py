from sqlalchemy.orm import Session
from app.domain.support import models, schemas
from typing import Literal

async def create_issue(db: Session, issue: schemas.BaseIssue, user_id: int):
    db_issue = models.Issue(reported_by_id=user_id, status='Nowe', **issue.model_dump())
    
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    
    return db_issue

async def get_issues_by_user_id(db: Session, user_id: int, sort_order: Literal['asc', 'desc'] = 'desc'):
    db_issues = db.query(models.Issue).filter(models.Issue.reported_by_id == user_id)
    if sort_order == 'asc':
        return db_issues.order_by(models.Issue.updated_at.asc()).all()
    else:
        return db_issues.order_by(models.Issue.updated_at.desc()).all()
    
async def get_issue_by_user_and_issue_id(db: Session, issue_id: int, user_id: int):
    return db.query(models.Issue).filter(models.Issue.id == issue_id).filter(models.Issue.reported_by_id == user_id).first()