import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from src.dependency import DbSession
from src.auth.schemas import RegisterUserRequest, TokenData, Tokens
from src.entities.users import Users
import logging
from starlette import status
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
import jwt
from jwt.exceptions import PyJWTError
from uuid import UUID
from typing import Annotated
from fastapi import Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
JWT_ACCESS_TOKEN_TTL = int(os.getenv("JWT_ACCESS_TOKEN_TTL"))
JWT_REFRESH_TOKEN_TTL = int(os.getenv("JWT_REFRESH_TOKEN_TTL"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET not set in environment")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        return False


async def authenticate_user(
    email: str, password: str, db: AsyncSession
) -> Users | bool:

    try:
        result = await db.execute(select(Users).where(Users.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password):
            logging.warning(f"Failed authentication attempt for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wrong email or pass",
            )

        return user
    except Exception as e:
        logging.error(f"Error during authentication for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error",
        )


def create_access_token(
    email: str, user_id: UUID, expires_minutes: int = JWT_ACCESS_TOKEN_TTL
) -> str:

    try:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        payload = {"sub": email, "id": str(user_id), "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logging.error(f"Failed to create access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access token",
        )


def create_refresh_token(
    email: str, user_id: UUID, expires_days: int = JWT_REFRESH_TOKEN_TTL
) -> str:

    try:
        expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
        payload = {"sub": email, "id": str(user_id), "exp": expire, "type": "refresh"}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logging.error(f"Failed to create refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refresh token",
        )


def verify_token(token: str) -> TokenData:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        return TokenData(user_id=user_id)
    except PyJWTError as e:
        logging.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def create_user(db: AsyncSession, register_user_request: RegisterUserRequest):

    try:
        result_email = await db.execute(
            select(Users).where(Users.email == register_user_request.email)
        )
        existing_email = result_email.scalar_one_or_none()
        if existing_email:
            logging.warning(
                f"Registration failed: Email already exists: {register_user_request.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        result_username = await db.execute(
            select(Users).where(Users.username == register_user_request.username)
        )
        existing_username = result_username.scalar_one_or_none()
        if existing_username:
            logging.warning(
                f"Registration failed: Username already exists: {register_user_request.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        create_user_model = Users(
            email=register_user_request.email,
            username=register_user_request.username,
            password=get_password_hash(register_user_request.password),
        )
        db.add(create_user_model)
        await db.commit()
        await db.refresh(create_user_model)

        logging.info(f"Successfully registered user: {register_user_request.email}")
        return create_user_model

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to register user {register_user_request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> TokenData:
    return verify_token(token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


async def login(
    db: AsyncSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> Tokens:

    user = await authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )

    try:
        access_token = create_access_token(user.email, user.id)
        refresh_token = create_refresh_token(user.email, user.id)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            # secure=True,
            samesite="lax",
            max_age=JWT_REFRESH_TOKEN_TTL * 24 * 60 * 60,
        )

        return Tokens(access_token=access_token, token_type="bearer")
    except Exception as e:
        logging.error(f"Failed during login token creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error",
        )


def refresh_access_token(refresh_token: str) -> Tokens:

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        email: str = payload.get("sub")
        id: str = payload.get("id")

        if not email or not id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        new_access_token = create_access_token(email, user_id=UUID(id))
        return Tokens(access_token=new_access_token, token_type="bearer")

    except PyJWTError as e:
        logging.warning(f"Refresh token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    except Exception as e:
        logging.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh access token",
        )
