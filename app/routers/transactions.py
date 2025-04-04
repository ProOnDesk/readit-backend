import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session
from app.domain.article.service import get_article_by_id
from app.domain.support import service, schemas, models
from app.dependencies import get_db, authenticate, DefaultErrorModel, DefaultResponseModel, Responses, CreateExampleResponse, Example
from typing import Annotated, Union, Literal, Optional
from pydantic import BaseModel, EmailStr
from app.domain.transaction.schemas import Transaction, TransactionCreate, TransactionItemCreate
from app.domain.transaction.service import create_transaction, create_transaction_item, get_transaction, get_transaction_items_by_transaction_id, get_user_transactions_service
import os
import httpx
import uuid

from app.domain.user.schemas import User
from app.domain.user.service import get_user

router = APIRouter(
    prefix='/transactions',
    tags=['Transactions']
)

class PayUOrderCreate(BaseModel):
    amount: int  # amount in grosze, e.g., 1000 = 10 PLN
    buyer_email: EmailStr
    redirect_url: str = "http://127.0.0.1:8000/docs"


async def get_access_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYU_BASE_URL}/pl/standard/user/oauth/authorize",
            data={"grant_type": "client_credentials"},
            auth=(os.getenv("PAYU_CLIENT_ID"), os.getenv("PAYU_CLIENT_SECRET")),
        )
        response.raise_for_status()
        return response.json()["access_token"]

PAYU_BASE_URL = "https://secure.snd.payu.com" if os.getenv("PAYU_ENV") == "sandbox" else "https://secure.payu.com"
    
async def create_test_payu_order(
    amount: int, 
    buyer_email: str, 
    redirect_url: str,
    user_id: int = 1
):
    order_id = str(uuid.uuid4())
    token = await get_access_token()
    payload = {
        "notifyUrl": "http://readit.ddns.net:8000/transactions/notify",
        "customerIp": "127.0.0.1",
        "merchantPosId": os.getenv("PAYU_POS_ID"),
        "description": "Order description",
        "currencyCode": "PLN",
        "totalAmount": str(amount),
        "extOrderId": order_id,
        "continueUrl": redirect_url,
        "buyer": {
            "extCustomerId": str(user_id),
            "email": buyer_email,
            "language": "pl"
        },
        "products": [
            {
                "name": "Example product",
                "unitPrice": str(amount),
                "quantity": "1"
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYU_BASE_URL}/api/v2_1/orders",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Optional: manually handle 302
        if response.status_code in [200, 201, 302]:
            return response.json()
        
        response.raise_for_status()


async def create_payu_order(
    products: list[dict],
    user: User,
    redirect_url: str,
    order_id: str,
    total_price: int
):
    token = await get_access_token()
    payload = {
        "notifyUrl": "http://readit.ddns.net:8000/transactions/notify",
        "customerIp": "127.0.0.1",
        "merchantPosId": os.getenv("PAYU_POS_ID"),
        "description": f"Purchase by {user.first_name} {user.last_name} of {len(products)} articles.",
        "currencyCode": "PLN",
        "totalAmount": str(total_price),
        "extOrderId": order_id,
        "continueUrl": redirect_url,
        "buyer": {
            "extCustomerId": str(user.id),
            "email": user.email,
            "language": "pl"
        },
        "products": products
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYU_BASE_URL}/api/v2_1/orders",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Optional: manually handle 302
        if response.status_code in [200, 201, 302]:
            return response.json()
        
        response.raise_for_status()
    


@router.post("/notify")
async def payment_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.json()
    # print("Payment notification:", body)
    # print(body.get("order").get("extOrderId"))
    # print(body.get("order").get("status"))

    if not (order := get_transaction(db, body.get("order").get("extOrderId"))):
        return {"status": "OK"}
    

    order.status = body.get("order").get("status")
    db.commit()

    # Verify signature if needed and update order status
    return {"status": "OK"}



@router.post(
    "/create-test-order", 
    summary="Create test PayU order"
)
async def create_test_order(
    order: PayUOrderCreate
):
    try:
        result = await create_test_payu_order(
            order.amount,
            order.buyer_email, 
            order.redirect_url
        )

        redirect_uri = result.get("redirectUri")

        return {
            "status": "success",
            "redirect_url": redirect_uri,
            "PayUOrderId": result.get("orderId")
        }
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PayU Error: {e.response.text}"
        )
    
class CreateOrderResponse(BaseModel):   
    status: str
    redirect_url: str | None
    PayU_order_id: str | None
    order_id: str

@router.post(
    "/create-order",
    summary="Create PayU Order"
)
async def create_order(
    items: Annotated[list[int], Body()],
    redirect_url: Annotated[str, Body()],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> CreateOrderResponse:
    try:
        if not (user := get_user(db, user_id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Użytkownik nie istnieje'
            )
        
        articles = [get_article_by_id(db, item) for item in items]

        order_id = uuid.uuid4().__str__()

        total_price = 0

        for article in articles: total_price += int(article.price * 100)

        
        if total_price > 0:
            result = await create_payu_order(
                user=user,
                products=[{
                    "name": article.title,
                    "unitPrice": str(int(article.price * 100)),
                    "quantity": 1,
                    "vritual": True
                } for article in articles],
                redirect_url=redirect_url,
                order_id=order_id,
                total_price=total_price
            )

            redirect_uri = result.get("redirectUri")

        # print(result.get("orderId"))
        transaction = create_transaction(db, TransactionCreate(
            id=order_id,
            user_id=user_id,
            status="PENDING" if total_price > 0 else "COMPLETED",
            payu_order_id=result.get("orderId") if total_price > 0 else None,
            created_at=datetime.datetime.now()
        ))

        for article in articles:
            create_transaction_item(db, TransactionItemCreate(
                transaction_id=transaction.id,
                article_id=article.id,
                paid_out=True if article.is_free else False
            ))

        db.commit()

        return {
            "status": "success",
            "redirect_url": redirect_uri if total_price > 0 else None,
            "PayU_order_id": result.get("orderId") if total_price > 0 else None,
            "order_id": order_id
        }
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PayU Error: {e.response.text}"
        )
    

class StatusResponse(BaseModel):
    status: str = "PENDING"

@router.get(
    "/order-status/{order_id}"
)
async def get_order_status(
    order_id: str,
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> StatusResponse:
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )
    
    if not (order := get_transaction(db, order_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Zamówienie nie istnieje'
        )
    
    return {"status": order.status}


class TransactionItemSummary(BaseModel):
    id: int
    title: str
    price: float


class UserTransaction(BaseModel):
    id: str
    status: str
    created_at: datetime.datetime
    total_price: float
    items: list[TransactionItemSummary]

@router.get(
    "/user-transactions",
    response_model=Page[UserTransaction],
)
async def get_user_transactions(
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> Page[UserTransaction]:

    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )

    transactions = get_user_transactions_service(db, user_id)

    output = []
    for transaction in transactions:
        t_items = get_transaction_items_by_transaction_id(db, transaction.id)
        items = []
        for item in t_items:
            article = item.article
            items.append(TransactionItemSummary(
                id=item.id,
                title=article.title,
                price=article.price
            ))

        output.append(UserTransaction(
            id=transaction.id,
            status=transaction.status,
            created_at=transaction.created_at,
            total_price=transaction.total_price,
            items=items
        ))

    return paginate(output)