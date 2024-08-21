from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    expiration_date: datetime
    token_type: str