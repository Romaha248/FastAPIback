from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.todos.router import router as todos_router


def register_routes(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(todos_router)
