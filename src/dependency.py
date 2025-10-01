from fastapi import Depends
from src.database.dbcore import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, AsyncGenerator


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]
