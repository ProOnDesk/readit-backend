from sqladmin import ModelView
from .models import Article, Tag, ArticleComment, WishList, ArticleContentElement, Collection, CollectionArticle, ArticlePurchase

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
        'rating',
    ]
    form_columns = [
        'author_id', 
        'article_id',
        'content',
        'author',
        'article',
        'rating'
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
        'owner_id', 
        'title', 
        'short_description',
        'discount_percentage',
        'collection_image',
        'articles_count',  # Custom property from the model
        'price',  # Custom property from the model
        'created_at',
        'updated_at'
    ]
    form_columns = [
        'owner_id',
        'title',
        'short_description',
        'discount_percentage',
        'collection_image',
        'articles'
    ]
class CollectionView(ModelView, model=Collection):
    column_list = [
        
    ]
    
class CollectionArticleView(ModelView, model=CollectionArticle):
    column_list = [
        'id', 
        'collection_id', 
        'article_id'
    ]
    form_columns = [
        'collection_id',
        'article_id'
    ]

class ArticlePurchaseView(ModelView, model=ArticlePurchase):
    column_list = [
        "id",
        "user_id",
        "article_id"
    ]