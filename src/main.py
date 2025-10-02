from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.dbcore import Base, engine
from src.entities import users, todos
from src.api import register_routes

app = FastAPI()

Base.metadata.create_all(bind=engine)

origins = ["http://localhost:3000", "https://nextjsfront.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)
