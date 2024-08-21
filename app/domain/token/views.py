from sqladmin import Admin, ModelView
from .models import Token

class TokenView(ModelView, model=Token):
    column_list = [
        'refresh_token', 'access_token', 'expiration_date', 'token_type'
    ]
