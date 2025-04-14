from sqladmin import Admin, ModelView
from .models import Transaction, TransactionItem

class TransactionView(ModelView, model=Transaction):
    column_list = [
        "id", "user_id", "status", "created_at", "payu_order_id"
    ]

class TransactionItemView(ModelView, model=TransactionItem):
    column_list = [
        "id", "transaction_id", "article_id", "paid_out"
    ]