from sqladmin import Admin, ModelView
from .models import User, Follower, Skill, SkillList

class UserView(ModelView, model=User):
    column_list = [
        'id', 'first_name', 'last_name', 'email', 'sex', 'avatar', 'follower_count', 'following_count', 'background_image', 'description', 'short_description', "is_active", 'hashed_password'
    ]

class FollowerView(ModelView, model=Follower):
    column_list = [
        'id', 'followed_id', 'follower_id'
    ]

class SkillView(ModelView, model=Skill):
    column_list = [
        'id', 'skill_name'
    ]

class SkillListView(ModelView, model=SkillList):
    column_list = [
        'id', 'user_id', 'skill_id'
    ]

