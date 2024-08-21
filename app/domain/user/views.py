from sqladmin import Admin, ModelView
from .models import User, Item

class UserView(ModelView, model=User):
    column_list = [
        'id', 'email', 'hashed_password', 'is_active'
    ]

class ItemView(ModelView, model=Item):
    column_list = [
        'id', 'title', 'description', 'owner_id'
    ]

