from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.middleware import get_current_user
from backend.auth.models import TokenResponse, UserLogin, UserOut, UserRegister
from backend.config import (
    JWT_ACCESS_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_EXPIRE_DAYS,
    JWT_SECRET,
)
from backend.memory.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${pwd_hash.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, pwd_hash = stored.split("$", 1)
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return new_hash.hex() == pwd_hash
    except (ValueError, AttributeError):
        return False


def _create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "exp": expire, "type": "access"},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    token = jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh", "jti": secrets.token_hex(16)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return token


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister):
    db = await get_db()
    existing = await db.execute_fetchall(
        "SELECT id FROM users WHERE username = ?", (body.username,)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    password_hash = _hash_password(body.password)
    cursor = await db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (body.username, password_hash),
    )
    await db.commit()
    user_id = cursor.lastrowid

    access_token = _create_access_token(user_id, body.username)
    refresh_token = _create_refresh_token(user_id)

    # Store refresh token hash
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expire.isoformat()),
    )
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (body.username,),
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    user = rows[0]
    if not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = _create_access_token(user["id"], user["username"])
    refresh_token = _create_refresh_token(user["id"])

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user["id"], token_hash, expire.isoformat()),
    )
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: dict):
    raw_token = body.get("refresh_token", "")
    if not raw_token:
        raise HTTPException(status_code=400, detail="refresh_token required")

    try:
        payload = jwt.decode(raw_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload["sub"])

    # Verify refresh token exists and not revoked
    db = await get_db()
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    rows = await db.execute_fetchall(
        "SELECT id FROM refresh_tokens WHERE token_hash = ? AND revoked = 0",
        (token_hash,),
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")

    # Revoke old refresh token (rotation)
    await db.execute(
        "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
        (token_hash,),
    )

    # Get username
    user_rows = await db.execute_fetchall(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    )
    if not user_rows:
        raise HTTPException(status_code=404, detail="User not found")

    username = user_rows[0]["username"]
    new_access = _create_access_token(user_id, username)
    new_refresh = _create_refresh_token(user_id)

    new_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, new_hash, expire.isoformat()),
    )
    await db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut(id=user["id"], username=user["username"], created_at="")
