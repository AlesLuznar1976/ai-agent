from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import verify_token
from app.models import TokenData, Permission


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Pridobi trenutnega uporabnika iz JWT tokena"""

    token = credentials.credentials
    token_data = verify_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neveljaven ali potekel token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


def require_permission(permission: Permission):
    """Dependency za preverjanje dovoljenj"""

    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if permission.value not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nimate dovoljenja: {permission.value}"
            )
        return current_user

    return permission_checker


def require_any_permission(*permissions: Permission):
    """Dependency za preverjanje vsaj enega od dovoljenj"""

    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        user_permissions = set(current_user.permissions)
        required = set(p.value for p in permissions)

        if not user_permissions & required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nimate nobenega od zahtevanih dovoljenj"
            )
        return current_user

    return permission_checker
