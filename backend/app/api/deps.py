from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import Role, User
from app.db.session import get_db
from app.services.audit import write_audit

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: Role) -> Callable[[Request, User, Session], User]:
    def dependency(
        request: Request,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if user.role not in roles:
            write_audit(
                db,
                user.id,
                "permission.denied",
                "rbac",
                None,
                {"required_roles": [role.value for role in roles], "actual_role": user.role.value},
                request,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency

