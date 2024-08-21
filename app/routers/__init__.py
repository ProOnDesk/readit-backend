from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..dependencies import get_db
from app.domain.user.service import get_user_by_email_and_hashed_password
from app.config import SECRET_KEY, ENCRYPTION_ALGORITHM
import jwt

router = APIRouter(
    prefix="",
    tags=["Root"],
    responses={404: {'description': 'Not found'}},
)

### Default request
# @router.get("/")
# async def root(db: Session = Depends(get_db)) -> dict:
#     try:
#         from app.domain.user.service import get_user
#         print(get_user(db, 1))
#     except Exception as e:
#         print(f'{e}')
#     return {"hello": "world"}

### Websocket + testing if it works
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
async def get(
    user: Annotated[str | None, Query(title="User to confirm")],
    db: Session = Depends(get_db)
):
    if user:
        try:
            decoded_user = jwt.decode(user, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
            if not (current_user := get_user_by_email_and_hashed_password(db, decoded_user.get("email"), decoded_user.get("password"))):
                raise HTTPException(status_code=400)
        
            current_user.is_active = True
            db.commit()
        except:
            raise HTTPException(status_code=400)

    return HTMLResponse(html)

@router.websocket("/")
async def websocker_root(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except Exception as e:
            print(f'Error has occured:\n\n{e}')
            break


