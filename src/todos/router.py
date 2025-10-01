from fastapi import APIRouter, Query
from src.todos.service import (
    new_todo,
    get_user_todos,
    get_todo_by_id,
    delete_todo_by_id,
    update_todo_by_id,
)
from src.enums.todos import TodoCategory
from src.dependency import DBSession
from src.todos.schemas import TodoRequest
from src.auth.service import CurrentUser

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/all-todo")
async def get_all_todos(
    db: DBSession,
    current_user: CurrentUser,
    category: TodoCategory | None = Query(None),
    sort_order: str = Query("asc", description="Sort by priority: 'asc' or 'desc'"),
    search: str | None = Query(
        None, description="Search todos by title or description"
    ),
):
    return await get_user_todos(db, current_user, category, sort_order, search)


@router.get("/single-todo/{todo_id}")
async def get_single_todo(db: DBSession, current_user: CurrentUser, todo_id: str):
    return await get_todo_by_id(db, current_user, todo_id)


@router.post("/create-todo")
async def create_todo(
    db: DBSession, todo_request: TodoRequest, current_user: CurrentUser
):
    return await new_todo(db, todo_request, current_user)


@router.patch("/update-todo/{todo_id}")
async def update_todo(
    db: DBSession, todo_request: TodoRequest, current_user: CurrentUser, todo_id: str
):
    return await update_todo_by_id(db, todo_request, current_user, todo_id)


@router.delete("/delete-todo/{todo_id}")
async def delete_todo(db: DBSession, current_user: CurrentUser, todo_id: str):
    return await delete_todo_by_id(db, current_user, todo_id)
