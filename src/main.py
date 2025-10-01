from fastapi import FastAPI
from src.database.dbcore import Base, engine
from src.entities import users, todos
from src.api import register_routes

app = FastAPI()

Base.metadata.create_all(bind=engine)

register_routes(app)
