from sqladmin import Admin, ModelView
from .models import Article, Tag, ArticleComment

class ArticleView(ModelView, model=Article):
    column_list = [
        'id', 'title', 'slug', 'language', 'content', 'summary', 'author', 'created_at', 'view_count', 'tags'
    ]
    form_columns = [
        'title', 'language', 'content', 'summary', 'author', 'tags'
    ]

    
class TagView(ModelView, model=Tag):
    column_list = [
        'id',
        'value'
    ]
    form_columns=[
        'value'
    ]
    
class ArticleCommentView(ModelView, model=ArticleComment):
    column_list = [
        'id',
        'author_id',
        'article_id',
        'content',
        'created_at'
    ]
    form_columns = [
        'author_id',
        'article_id',
        'content',
    ]
