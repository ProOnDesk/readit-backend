import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DB_URL")
CORS_ORIGINS = [
    "*",
]

ACCESS_TOKEN_EXPIRE_TIME = 60 # in minutes

### Hashing
SECRET_KEY = os.environ.get("SECRET_KEY") # if you don't have one, you can generate one using `openssl rand -hex 32` in cmd
ENCRYPTION_ALGORITHM = "HS256"

