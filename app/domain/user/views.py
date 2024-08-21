from sqladmin import Admin, ModelView
from .models import User

class UserView(ModelView, model=User):
    column_list = [
        'id', 'email', 'hashed_password', 'is_active'
    ]