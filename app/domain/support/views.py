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
    
    column_searchable_list = [Issue.title, Issue.category, Issue.status]
    
    form_columns = [
        'category',
        'title',
        'description',
        'status',
        'reported_by_id' 
    ]
    
    