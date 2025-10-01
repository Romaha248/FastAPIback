from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dbcore import AsyncSessionLocal
from typing import Annotated


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
