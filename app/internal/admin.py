from sqladmin import Admin, ModelView
from app.database import engine, SessionLocal
from app.domain.article.views import TagView, ArticleView
from app.domain.user.views import UserView, FollowerView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
import os

class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        form = await request.form()

        if form.get('username') != os.environ.get("ADMIN_LOGIN") or form.get('password') != os.environ.get("ADMIN_PASSWORD"):
            return False

        request.session.update({"token": form.get('username')})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return token is not None

def create_admin(app):
    authentication_backend = AdminAuth(secret_key="supersecretkey")
    admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

    admin.add_view(UserView)
    admin.add_view(ArticleView)
    admin.add_view(TagView)
    admin.add_view(FollowerView)
    
    return admin