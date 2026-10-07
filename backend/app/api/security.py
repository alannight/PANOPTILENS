import hmac
import os

from fastapi import Header, HTTPException, status


def require_admin_password(password: str | None = Header(default=None, alias="X-Admin-Password")) -> None:
    expected_password = os.getenv("ADMIN_PASSWORD", "Admin1234")
    if password is None or not hmac.compare_digest(
        password.encode("utf-8"), expected_password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin password",
        )