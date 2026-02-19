from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import verify_password, hash_password, create_tokens, verify_token, get_current_user
from app.models import Token, TokenData, UserRole
from app.database import get_db
from app.crud.uporabniki import get_uporabnik_by_username, get_uporabnik_by_id, update_zadnja_prijava

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Prijava uporabnika"""

    db_user = get_uporabnik_by_username(db, request.username)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Napačno uporabniško ime ali geslo"
        )

    if not db_user.aktiven:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Uporabniški račun je deaktiviran"
        )

    if not verify_password(request.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Napačno uporabniško ime ali geslo"
        )

    # Posodobi zadnjo prijavo
    update_zadnja_prijava(db, db_user.id)

    tokens = create_tokens(
        user_id=db_user.id,
        username=db_user.username,
        role=UserRole(db_user.vloga)
    )

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest):
    """Osveži access token"""

    token_data = verify_token(request.refresh_token, expected_type="refresh")

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neveljaven refresh token"
        )

    tokens = create_tokens(
        user_id=token_data.user_id,
        username=token_data.username,
        role=token_data.role
    )

    return tokens


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pridobi podatke o trenutnem uporabniku"""

    db_user = get_uporabnik_by_id(db, current_user.user_id)

    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "permissions": current_user.permissions,
        "mailbox": db_user.mailbox if db_user else None,
    }


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """Odjava uporabnika"""
    # V produkciji bi tukaj dodali token na blacklist
    return {"message": "Uspešna odjava"}
