from fastapi import APIRouter, status
from uuid import UUID
from src.users.schemas import UserResponse, PasswordChange
from src.dependency import DBSession
from src.auth.service import CurrentUser
from src.users.service import get_user_by_id, change_pass


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser, db: DBSession):
    return await get_user_by_id(db, current_user.get_uuid())


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange, db: DBSession, current_user: CurrentUser
):
    await change_pass(db, current_user.get_uuid(), password_change)
    return {"message": "Password changed successfully."}
