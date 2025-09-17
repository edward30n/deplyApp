"""
Security utilities for JWT token handling, password hashing, and authentication
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
import hashlib
import hmac
import json
import base64
import jwt
import secrets
import string

from sqlalchemy.orm import Session
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using simple SHA256."""
    # Simple hash for now - in production use bcrypt
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password using simple SHA256."""
    # Simple hash for now - in production use bcrypt
    return hashlib.sha256(password.encode()).hexdigest()

def generate_reset_token() -> str:
    """Generate a secure random token for password reset"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with 30-day expiration
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def store_token_in_db(db: Session, user_id: int, token: str, expires_at: datetime):
    """
    Store token in database for tracking and potential revocation
    """
    # Import here to avoid circular imports
    from app.models.user import AuthToken
    
    # Remove existing tokens for this user
    db.query(AuthToken).filter(
        AuthToken.user_id == user_id,
        AuthToken.revoked == False
    ).update({"revoked": True})
    
    # Create new token record
    token_obj = AuthToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        revoked=False
    )
    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)
    return token_obj

def revoke_token(db: Session, token: str):
    """
    Revoke a token by marking it as revoked in the database
    """
    # Import here to avoid circular imports
    from app.models.user import AuthToken
    
    token_obj = db.query(AuthToken).filter(
        AuthToken.token == token,
        AuthToken.revoked == False
    ).first()
    
    if token_obj:
        token_obj.revoked = True
        db.commit()
        return True
    return False

def is_token_revoked(db: Session, token: str) -> bool:
    """
    Check if a token has been revoked
    """
    # Import here to avoid circular imports
    from app.models.user import AuthToken
    
    token_obj = db.query(AuthToken).filter(
        AuthToken.token == token
    ).first()
    
    return token_obj.revoked if token_obj else True

def get_user_from_token(db: Session, token: str):
    """Get user from token."""
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None
    
    # Import here to avoid circular imports
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    return user
