from fastapi import HTTPException
from src.todos.schemas import TodoRequest, TodoResponse, UpdateTodoRequest
from src.entities.todos import Todos
from src.auth.service import CurrentUser
from src.enums.todos import TodoCategory
from sqlalchemy.future import select
from sqlalchemy import asc, desc, and_
import logging
from sqlalchemy.orm import Session


def get_user_todos(
    db: Session,
    user: CurrentUser,
    category: TodoCategory | None,
    sort_order: str,
    search: str | None,
) -> list[TodoResponse]:

    if not user:
        logging.warning("Unauthorized access attempt to get_user_todos")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todos_query = db.query(Todos).filter(Todos.user_id == user.user_id)

        if category:
            todos_query = todos_query.filter(Todos.categories == category)

        if search:
            search_pattern = f"%{search}%"
            todos_query = todos_query.filter(
                (Todos.title.ilike(search_pattern))
                | (Todos.description.ilike(search_pattern))
            )

        if sort_order.lower() == "asc":
            todos_query = todos_query.order_by(Todos.priority.asc())
        else:
            todos_query = todos_query.order_by(Todos.priority.desc())

        todos = todos_query.all()

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


def get_todo_by_id(db: Session, user: CurrentUser, todo_id: str) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to get_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todo = (
            db.query(Todos)
            .filter(Todos.id == todo_id)
            .filter(Todos.user_id == user.user_id)
            .first()
        )

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


def new_todo(db: Session, todo_request: TodoRequest, user: CurrentUser) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to new_todo")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todo_data = todo_request.model_dump()
        new_todo = Todos(**todo_data, user_id=user.user_id)

        db.add(new_todo)
        db.commit()

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


def update_todo_by_id(
    db: Session, todo_request: UpdateTodoRequest, user: CurrentUser, todo_id: str
) -> TodoResponse:

    if not user:
        logging.warning("Unauthorized access attempt to update_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todo = (
            db.query(Todos)
            .filter(and_(Todos.id == todo_id, Todos.user_id == user.user_id))
            .first()
        )

        if not todo:
            logging.warning(f"Todo not found for update: {todo_id} user {user.user_id}")
            raise HTTPException(status_code=404, detail="Todo not found")

        update_data = todo_request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(todo, key, value)

        db.add(todo)
        db.commit()

        logging.info(f"Updated todo {todo_id} for user {user.user_id}")
        return TodoResponse.model_validate(todo)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating todo {todo_id} for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update todo")


def delete_todo_by_id(db: Session, user: CurrentUser, todo_id: str) -> bool:

    if not user:
        logging.warning("Unauthorized access attempt to delete_todo_by_id")
        raise HTTPException(status_code=401, detail="Auth failed")

    try:
        todo = (
            db.query(Todos)
            .filter(and_(Todos.id == todo_id, Todos.user_id == user.user_id))
            .first()
        )

        if not todo:
            logging.warning(
                f"Todo not found for deletion: {todo_id} user {user.user_id}"
            )
            raise HTTPException(status_code=404, detail="Todo not found")

        db.delete(todo)
        db.commit()

        logging.info(f"Deleted todo {todo_id} for user {user.user_id}")
        return True

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting todo {todo_id} for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete todo")
