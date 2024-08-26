from sqladmin import ModelView
from .models import Article, Tag, ArticleComment, WishList, ArticleContentElement

class ArticleView(ModelView, model=Article):
    column_list = [
        'id',
        'title',
        'slug',
        'summary',
        'author', 
        'created_at',
        'view_count',
        'tags',
        'title_image'
    ]
    form_columns = [
        'title',
        'summary',
        'author', 
        'tags',       
        'title_image',
        'price',
        'is_free'

    ]

class TagView(ModelView, model=Tag):
    column_list = [
        'id',
        'value'
    ]
    form_columns = [
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
        'content'
    ]

class WishListView(ModelView, model=WishList):
    column_list = [
        'id', 
        'user_id', 
        'article_id',
        'created_at'
    ]

class ArticleContentElementView(ModelView, model=ArticleContentElement):
    column_list = [
        'id', 
        'article_id', 
        'content_type',
        'content', 
        'order'
    ]
