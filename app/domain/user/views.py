from sqladmin import Admin, ModelView
from .models import User

class UserView(ModelView, model=User):
    column_list = [
        'id', 'email', 'sex', 'avatar', 'short_description', 'origin', 'language','hashed_password'
    ]