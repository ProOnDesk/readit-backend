from sqladmin import Admin, ModelView
from .models import User, Follower

class UserView(ModelView, model=User):
    column_list = [
        'id', 'first_name', 'last_name', 'email', 'sex', 'avatar', 'short_description', 'origin', 'language', "is_active", 'hashed_password'
    ]

class FollowerView(ModelView, model=Follower):
    column_list = [
        'id', 'followed_id', 'follower_id'
    ]