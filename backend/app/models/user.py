from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from app.database.session import Base

class Country(Base):
    __tablename__ = "countries"
    
    code = Column(String(2), primary_key=True, index=True, nullable=False)  # CO, US, etc.
    name = Column(String(100), nullable=False)  # Colombia, United States, etc.
    
    def __repr__(self):
        return f"<Country(code='{self.code}', name='{self.name}')>"

class User(Base):
    __tablename__ = "users"

    # Coincide exactamente con la estructura de la BD
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(Text, nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    country_code = Column(String(2), default='CO', nullable=False)
    phone_prefix = Column(String(10), nullable=True)
    
    # Relaciones (usando strings para evitar circular imports)
    company = relationship("Company", back_populates="users")
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    # Coincide exactamente con la estructura de la BD
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    user = relationship("User", back_populates="auth_tokens")
    
    def __repr__(self):
        return f"<AuthToken(id={self.id}, user_id={self.user_id})>"
