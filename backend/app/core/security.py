"""Authentication helpers: password hashing and JWT tokens.

Uses bcrypt for password hashing (with a compatibility shim for both
bcrypt 3.x and 4.x APIs) and PyJWT for token issuance/validation.
"""
from __future__ import annotations

import datetime
import logging
import re

import jwt
from fastapi import Header

from . import config
from .exceptions import AuthenticationError, TokenError

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{1,39}$")


def _hash_password(password: str) -> str:
    import bcrypt

    salt = bcrypt.gensalt(rounds=12)
    if hasattr(bcrypt, "hashpw"):
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    else:  # pragma: no cover - bcrypt 3.x fallback
        hashed = bcrypt.encodepw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt

    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(password: str) -> str:
    """Return a bcrypt hash of ``password``."""
    return _hash_password(password)


def validate_password_strength(password: str) -> None:
    """Raise ``ValidationError`` if the password is too weak."""
    from .exceptions import ValidationError

    if not password or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one letter and one number")


def validate_email(email: str) -> None:
    from .exceptions import ValidationError

    if not email or not _EMAIL_RE.match(email):
        raise ValidationError("Invalid email address format")


def validate_username(username: str) -> None:
    """Raise ``ValidationError`` if the display username is invalid."""
    from .exceptions import ValidationError

    if not username or not username.strip():
        raise ValidationError("Username is required")
    if not _USERNAME_RE.match(username.strip()):
        raise ValidationError(
            "Username must be 2-40 characters and contain only letters, "
            "numbers, spaces, dots, underscores, or hyphens"
        )


def create_access_token(user_id: int, email: str) -> str:
    """Issue a JWT access token for ``user_id``."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=config.settings.jwt_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, config.settings.jwt_secret, algorithm=config.settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Validate and decode a JWT. Raises ``TokenError`` on failure."""
    try:
        payload = jwt.decode(
            token,
            config.settings.jwt_secret,
            algorithms=[config.settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc
    if payload.get("type") != "access":
        raise TokenError("Invalid token type")
    return payload


def get_user_id_from_token(token: str) -> int:
    payload = decode_token(token)
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise TokenError("Invalid token subject") from exc


def get_current_user_id(authorization: str | None) -> int:
    """Extract the authenticated user id from an ``Authorization`` header."""
    if not authorization:
        raise AuthenticationError("Missing authentication credentials")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Authorization header must be 'Bearer <token>'")
    return get_user_id_from_token(parts[1])


def get_current_user(authorization: str | None = Header(None, alias="Authorization")) -> int:
    """FastAPI dependency to authenticate and return the current user's ID."""
    user_id = get_current_user_id(authorization)
    from ..models.users import get_user_by_id
    user = get_user_by_id(user_id)
    if user is None:
        raise AuthenticationError("User account no longer exists")
    return user_id
