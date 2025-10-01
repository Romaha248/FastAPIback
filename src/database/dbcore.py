from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("POSTGRES_URL")

engine = create_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from src.entities import users, todos

# import contextlib
# from typing import Any, AsyncIterator

# from sqlalchemy.ext.asyncio import (
#     AsyncConnection,
#     AsyncSession,
#     async_sessionmaker,
#     create_async_engine,
# )
# from sqlalchemy.orm import DeclarativeBase
# import os
# import re
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("POSTGRES_URL")

# if not DATABASE_URL:
#     raise ValueError("POSTGRES_URL is not set in environment")

# DATABASE_URL = re.sub(r"^postgresql:", "postgresql+asyncpg:", DATABASE_URL)


# class Base(DeclarativeBase):
#     __mapper_args__ = {"eager_defaults": True}


# class DatabaseSessionManager:
#     def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
#         self._engine = create_async_engine(host, **engine_kwargs)
#         self._sessionmaker = async_sessionmaker(
#             autocommit=False, bind=self._engine, expire_on_commit=False
#         )

#     async def close(self):
#         if self._engine is None:
#             raise Exception("DatabaseSessionManager is not initialized")
#         await self._engine.dispose()

#         self._engine = None
#         self._sessionmaker = None

#     @contextlib.asynccontextmanager
#     async def connect(self) -> AsyncIterator[AsyncConnection]:
#         if self._engine is None:
#             raise Exception("DatabaseSessionManager is not initialized")

#         async with self._engine.begin() as connection:
#             try:
#                 yield connection
#             except Exception:
#                 await connection.rollback()
#                 raise

#     @contextlib.asynccontextmanager
#     async def session(self) -> AsyncIterator[AsyncSession]:
#         if self._sessionmaker is None:
#             raise Exception("DatabaseSessionManager is not initialized")

#         session = self._sessionmaker()
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()


# sessionmanager = DatabaseSessionManager(DATABASE_URL, {"echo": True})


# async def get_db_session():
#     async with sessionmanager.session() as session:
#         yield session
