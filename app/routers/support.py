from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session
from app.domain.support import service, schemas, models
from app.dependencies import get_db, authenticate, DefaultErrorModel, DefaultResponseModel, Responses, CreateExampleResponse, Example
from typing import Annotated, Union, Literal, Optional

router = APIRouter(
    prefix='/support',
    tags=['Support']
)

@router.post(
    '/issue',
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(issue: schemas.BaseIssue, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> schemas.IssueOut:
    return await service.create_issue(db=db, issue=issue, user_id=user_id)

@router.get(
    '/issue/list',
    status_code=status.HTTP_200_OK
)
async def get_my_issue_list(user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)], sort_order: Literal['desc', 'asc'] = Query('desc', description='Sort the issues by the "updated_at" field')) -> Page[schemas.IssueOut]:
    db_issues = await service.get_issues_by_user_id(db=db, user_id=user_id, sort_order=sort_order)

    return paginate(db_issues)

@router.get(
    '/issue/{issue_id}',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description='Not Found',
            content_type='application/json',
            examples=[
                Example(
                    name='IssueNotFound',
                    summary='Issue not Found',
                    descriptio='The issue with given ID does not exsits.',
                    value=DefaultErrorModel(detail='Nie znaleziono zgłoszenia.')
                )
            ]
        )
    )
)
async def get_my_issue_by_id(issue_id: int, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> schemas.IssueOut:
    db_issue = await service.get_issue_by_user_and_issue_id(db=db, issue_id=issue_id, user_id=user_id)
    if not db_issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Nie znaleziono zgłoszenia.')
    return db_issue