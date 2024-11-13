from pydantic import BaseModel, constr
from datetime import datetime
from typing import Literal
from app.domain.user.schemas import UserBase

class UserIssue(BaseModel):
    id: int
    first_name: str
    last_name: str
    avatar_url: str

class BaseIssue(BaseModel):
    category: Literal['Naruszenie regulaminu', 'Problem techniczny', 'Prośba o pomoc']
    title: constr(max_length=255)
    description: str
    
class IssueOut(BaseIssue):
    id: int
    status: Literal['Nowe', 'W trakcie', 'Rozwiązane', 'Zamknięte']
    created_at: datetime
    updated_at: datetime
    reported_by: UserIssue
