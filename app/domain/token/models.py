from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from ...database import Base

class Token(Base):
    __tablename__ = "tokens"

    refresh_token = Column(String(36), primary_key=True, nullable=False)
    access_token = Column(String(36), unique=True, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    token_type = Column(String(20), nullable=False)

    def __repr__(self):
        return f'<Token access_token={self.token} refresh_token={self.refresh_token} expiration_date={self.expiration_date} token_type={self.token_type}>'