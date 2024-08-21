from sqlalchemy.orm import Session

from . import models, schemas

def get_token_by_resfresh_token(db: Session, refresh_token: str):
    return db.query(models.Token).filter(models.Token.refresh_token == refresh_token).first()

def get_token_by_access_token(db: Session, access_token: str):
    return db.query(models.Token).filter(models.Token.access_token == access_token).first()

def create_token(db: Session, token: schemas.Token):
    db_token = models.Token(access_token=token.access_token, refresh_token=token.refresh_token, expiration_date=token.expiration_date, token_type=token.token_type)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token