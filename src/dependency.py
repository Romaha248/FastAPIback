# from typing import AsyncGenerator
# from fastapi import Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from src.database.dbcore import AsyncSessionLocal
# from typing import Annotated


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()


# DbSession = Annotated[AsyncSession, Depends(get_db)]

from typing import Annotated

from src.database.dbcore import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DBSession = Annotated[AsyncSession, Depends(get_db_session)]
