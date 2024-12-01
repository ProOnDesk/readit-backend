from sqladmin import ModelView
from .models import Issue

class IssueView(ModelView, model=Issue):
    column_list = [
        Issue.id,
        Issue.category,
        Issue.title,
        Issue.description,
        Issue.status,
        Issue.reported_by_id,

    ]
    
    