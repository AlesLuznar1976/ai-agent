from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    PRODAJA = "prodaja"
    TEHNOLOGIJA = "tehnologija"
    PROIZVODNJA = "proizvodnja"
    NABAVA = "nabava"
    RACUNOVODSTVO = "racunovodstvo"
    READONLY = "readonly"


class Permission(str, Enum):
    # Projekti
    PROJECT_VIEW = "project:view"
    PROJECT_CREATE = "project:create"
    PROJECT_EDIT = "project:edit"
    PROJECT_DELETE = "project:delete"

    # Dokumenti
    DOCUMENT_VIEW = "document:view"
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_DELETE = "document:delete"

    # CalcuQuote
    CQ_VIEW = "calcuquote:view"
    CQ_SYNC = "calcuquote:sync"
    CQ_CREATE_RFQ = "calcuquote:create_rfq"

    # Largo
    LARGO_VIEW = "largo:view"
    LARGO_CREATE_DN = "largo:create_dn"
    LARGO_EDIT = "largo:edit"

    # Email
    EMAIL_VIEW = "email:view"
    EMAIL_SEND = "email:send"

    # Admin
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"


# Dovoljenja za vsako vlogo
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: list(Permission),

    UserRole.PRODAJA: [
        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_EDIT,
        Permission.DOCUMENT_VIEW,
        Permission.DOCUMENT_CREATE,
        Permission.CQ_VIEW,
        Permission.CQ_CREATE_RFQ,
        Permission.EMAIL_VIEW,
        Permission.EMAIL_SEND,
    ],

    UserRole.TEHNOLOGIJA: [
        Permission.PROJECT_VIEW,
        Permission.PROJECT_EDIT,
        Permission.DOCUMENT_VIEW,
        Permission.DOCUMENT_CREATE,
        Permission.CQ_VIEW,
        Permission.CQ_SYNC,
        Permission.LARGO_VIEW,
        Permission.LARGO_CREATE_DN,
        Permission.EMAIL_VIEW,
    ],

    UserRole.PROIZVODNJA: [
        Permission.PROJECT_VIEW,
        Permission.DOCUMENT_VIEW,
        Permission.LARGO_VIEW,
    ],

    UserRole.NABAVA: [
        Permission.PROJECT_VIEW,
        Permission.DOCUMENT_VIEW,
        Permission.CQ_VIEW,
        Permission.LARGO_VIEW,
        Permission.EMAIL_VIEW,
        Permission.EMAIL_SEND,
    ],

    UserRole.RACUNOVODSTVO: [
        Permission.PROJECT_VIEW,
        Permission.DOCUMENT_VIEW,
        Permission.LARGO_VIEW,
        Permission.LARGO_EDIT,
    ],

    UserRole.READONLY: [
        Permission.PROJECT_VIEW,
        Permission.DOCUMENT_VIEW,
    ],
}


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    ime: Optional[str] = None
    priimek: Optional[str] = None
    vloga: UserRole = UserRole.READONLY


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    ime: Optional[str] = None
    priimek: Optional[str] = None
    vloga: Optional[UserRole] = None
    aktiven: Optional[bool] = None


class User(UserBase):
    id: int
    aktiven: bool = True
    datum_ustvarjen: datetime
    zadnja_prijava: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    password_hash: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    username: str
    role: UserRole
    permissions: list[str]
