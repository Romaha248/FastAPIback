from fastapi import Depends
from src.database.dbcore import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]
