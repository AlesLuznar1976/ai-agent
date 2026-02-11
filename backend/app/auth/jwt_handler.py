from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from typing import Optional

from app.config import get_settings
from app.models import TokenData, UserRole, ROLE_PERMISSIONS


settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Preveri geslo"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def hash_password(password: str) -> str:
    """Hashiraj geslo"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def create_access_token(data: dict) -> str:
    """Ustvari access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Ustvari refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str, expected_type: str = "access") -> Optional[TokenData]:
    """Preveri token in vrne podatke"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        if payload.get("type") != expected_type:
            return None

        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")

        if user_id is None or username is None or role is None:
            return None

        # Pridobi dovoljenja za vlogo
        user_role = UserRole(role)
        permissions = [p.value for p in ROLE_PERMISSIONS.get(user_role, [])]

        return TokenData(
            user_id=user_id,
            username=username,
            role=user_role,
            permissions=permissions
        )

    except JWTError:
        return None


def create_tokens(user_id: int, username: str, role: UserRole) -> dict:
    """Ustvari oba tokena"""
    token_data = {
        "user_id": user_id,
        "username": username,
        "role": role.value
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }
