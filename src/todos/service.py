from fastapi import HTTPException
from src.todos.schemas import TodoRequest, TodoResponse
from src.entities.todos import Todos
from src.auth.service import CurrentUser
from src.enums.todos import TodoCategory
from sqlalchemy.future import select
from sqlalchemy import asc, desc
import logging
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_todos(
    db: AsyncSession,
    user: CurrentUser,
    category: TodoCategory | None,
    sort_order: str,
    search: str | None,
) -> list[TodoResponse]:

    if not user:
        logging.warning("Unauthorized access attempt to get_user_todos")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        query = select(Todos).where(Todos.user_id == user.user_id)

        if category:
            query = query.where(Todos.categories == category)

        if search:
            query = query.where(
                (Todos.title.ilike(f"%{search}%"))
                | (Todos.description.ilike(f"%{search}%"))
            )

        if sort_order.lower() == "asc":
            query = query.order_by(asc(Todos.priority))
        else:
            query = query.order_by(desc(Todos.priority))

        result = await db.execute(query)
        todos = result.scalars().all()

        logging.info(f"Retrieved {len(todos)} todos for user {user.user_id}")
        return [
            TodoResponse.model_validate(
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "categories": t.categories,
                    "priority": t.priority,
                    "complete": t.complete,
                    "deadline": t.deadline,
                }
            )
            for t in todos
        ]

    except Exception as e:
        logging.error(f"Error retrieving todos for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve todos")


async def get_todo_by_id(
    db: AsyncSession, user: CurrentUser, todo_id: str
) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to get_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        result = await db.execute(
            select(Todos)
            .where(Todos.id == todo_id)
            .where(Todos.user_id == user.user_id)
        )
        todo = result.scalar_one_or_none()

        if not todo:
            logging.warning(f"Todo not found: {todo_id} for user {user.user_id}")
            raise HTTPException(status_code=404, detail="Todo not found")

        return TodoResponse.model_validate(
            {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "categories": todo.categories,
                "priority": todo.priority,
                "complete": todo.complete,
                "deadline": todo.deadline,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving todo {todo_id} for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve todo")


async def new_todo(
    db: AsyncSession, todo_request: TodoRequest, user: CurrentUser
) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to new_todo")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todo_data = todo_request.model_dump()
        new_todo = Todos(**todo_data, user_id=user.user_id)

        db.add(new_todo)
        await db.commit()
        await db.refresh(new_todo)

        logging.info(f"Created new todo {new_todo.id} for user {user.user_id}")
        return TodoResponse.model_validate(
            {
                "id": new_todo.id,
                "title": new_todo.title,
                "description": new_todo.description,
                "categories": new_todo.categories,
                "priority": new_todo.priority,
                "complete": new_todo.complete,
                "deadline": new_todo.deadline,
            }
        )
    except Exception as e:
        logging.error(f"Error creating todo for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create todo")


async def update_todo_by_id(
    db: AsyncSession, todo_request: TodoRequest, user: CurrentUser, todo_id: str
) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to update_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        result = await db.execute(
            select(Todos)
            .where(Todos.id == todo_id)
            .where(Todos.user_id == user.user_id)
        )
        todo = result.scalar_one_or_none()

        if not todo:
            logging.warning(f"Todo not found for update: {todo_id} user {user.user_id}")
            raise HTTPException(status_code=404, detail="Todo not found")

        for field, value in todo_request.model_dump(exclude_unset=True).items():
            setattr(todo, field, value)

        await db.commit()
        await db.refresh(todo)

        logging.info(f"Updated todo {todo_id} for user {user.user_id}")
        return TodoResponse.model_validate(todo)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating todo {todo_id} for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update todo")


async def delete_todo_by_id(db: AsyncSession, user: CurrentUser, todo_id: str) -> bool:

    if not user:
        logging.warning("Unauthorized access attempt to delete_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        result = await db.execute(
            select(Todos)
            .where(Todos.id == todo_id)
            .where(Todos.user_id == user.user_id)
        )
        todo = result.scalar_one_or_none()

        if not todo:
            logging.warning(
                f"Todo not found for deletion: {todo_id} user {user.user_id}"
            )
            raise HTTPException(status_code=404, detail="Todo not found")

        await db.delete(todo)
        await db.commit()
        logging.info(f"Deleted todo {todo_id} for user {user.user_id}")
        return True

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting todo {todo_id} for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete todo")
