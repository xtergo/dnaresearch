"""
Authentication API Routes for DNA Research Platform
"""

from datetime import timedelta
from typing import List

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_DB,
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    username: str
    email: str
    role: str
    is_active: bool


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to get access token

    **Example Request:**
    ```
    POST /auth/login
    Content-Type: application/x-www-form-urlencoded

    username=admin&password=admin123
    ```

    **Example Response:**
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer"
    }
    ```
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login-json", response_model=Token)
async def login_json(credentials: LoginRequest):
    """
    JSON login endpoint for frontend

    **Example Request:**
    ```json
    {
        "username": "admin",
        "password": "admin123"
    }
    ```
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information

    **Example Response:**
    ```json
    {
        "username": "admin",
        "email": "admin@dnaresearch.com",
        "role": "admin",
        "is_active": true
    }
    ```
    """
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_current_active_user)):
    """
    List all users (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    users = []
    for user_data in USERS_DB.values():
        users.append(
            UserResponse(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=user_data["is_active"],
            )
        )
    return users


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """
    Register new user (simplified for MVP)

    **Example Request:**
    ```json
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "role": "user"
    }
    ```
    """
    if user_data.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Validate role
    if user_data.role not in ["user", "researcher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be one of: user, researcher, admin",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    USERS_DB[user_data.username] = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "role": user_data.role,
        "is_active": True,
    }

    return UserResponse(
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        is_active=True,
    )


@router.get("/test-users")
async def get_test_users():
    """
    Get test user credentials for development
    """
    return {
        "test_users": [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "researcher", "password": "research123", "role": "researcher"},
            {"username": "user", "password": "user123", "role": "user"},
        ],
        "note": "These are test credentials for development only",
    }
