"""
Security utilities: password hashing via PassLib and JWT token lifecycle.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=102400,
    argon2__time_cost=2,
    argon2__parallelism=8,
)


def _normalize_password(plain_password: Any) -> str:
    """Normalize and validate password candidates before hashing or verification."""
    if isinstance(plain_password, bytes):
        try:
            plain_password = plain_password.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TypeError("Password bytes must be UTF-8 decodable") from exc
    if not isinstance(plain_password, str):
        raise TypeError("Password must be a string")
    return plain_password


def hash_password(plain_password: Any) -> str:
    """Hash a plaintext password using Argon2."""
    password = _normalize_password(plain_password)
    utf8_len = len(password.encode("utf-8"))
    logger.debug(
        "Hashing password candidate: type=%s, utf8_length=%d bytes",
        type(password).__name__,
        utf8_len,
    )
    return pwd_context.hash(password)


def verify_password(plain_password: Any, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2 hash."""
    password = _normalize_password(plain_password)
    if not isinstance(hashed_password, str):
        raise TypeError("Hashed password must be a string")

    utf8_len = len(password.encode("utf-8"))
    logger.debug(
        "Verifying password candidate: type=%s, utf8_length=%d bytes, hash_length=%d",
        type(password).__name__,
        utf8_len,
        len(hashed_password),
    )
    return pwd_context.verify(password, hashed_password)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT with standard claims."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(subject: str, role: str) -> str:
    """Issue a short-lived access token embedding the user role for RBAC."""
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"role": role},
    )


def create_refresh_token(subject: str) -> str:
    """Issue a long-lived refresh token for session renewal."""
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        JWTError: When the token is invalid or expired.
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
