import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dbcore import Base, sessionmanager
from src.entities import users, todos
from src.api import register_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with sessionmanager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await sessionmanager._engine.dispose()


app = FastAPI(lifespan=lifespan)

register_routes(app)
