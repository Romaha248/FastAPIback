from src.dependency import DbSession
from src.users.schemas import UserResponse, PasswordChange
from src.entities.users import Users
from src.auth.service import get_password_hash, verify_password
from sqlalchemy.future import select
from starlette import status
from uuid import UUID
from fastapi import HTTPException
import logging


async def get_user_by_id(db: DbSession, user_id: UUID) -> Users:

    try:
        result = await db.execute(select(Users).where(Users.id == user_id))
        user = result.scalars().first()

        if not user:
            logging.warning(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        logging.info(f"Successfully retrieved user with ID: {user_id}")
        return user

    except Exception as e:
        logging.error(f"Error retrieving user with ID {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user.",
        )


async def change_pass(
    db: DbSession, user_id: UUID, change_pass: PasswordChange
) -> None:

    try:
        user = await get_user_by_id(db, user_id)

        if not verify_password(change_pass.current_password, user.password):
            logging.warning(f"Invalid current password for user ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password.",
            )

        if verify_password(change_pass.new_password, user.password):
            logging.warning(f"New password same as old password for user ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="New password cannot be the same as the old password.",
            )

        if change_pass.new_password != change_pass.new_password_confirm:
            logging.warning(f"Password confirmation mismatch for user ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match.",
            )

        try:
            user.password = get_password_hash(change_pass.new_password)
        except Exception as e:
            logging.error(f"Failed to hash password for user ID {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password.",
            )

        await db.commit()
        await db.refresh(user)
        logging.info(f"Password successfully changed for user ID: {user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"Unexpected error during password change for user ID {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password due to server error.",
        )
