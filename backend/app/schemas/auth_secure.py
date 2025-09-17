"""
Enhanced authentication schemas with security validations
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None

class CompanyRelationship(str, Enum):
    INDIVIDUAL = "individual"
    NEW_COMPANY = "new_company"
    JOIN_COMPANY = "join_company"

class CompanyCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None

# Enhanced User Creation
class UserCreate(UserBase):
    password: str
    company_id: Optional[int] = None
    accepted_terms: bool = False
    company_relationship: CompanyRelationship = CompanyRelationship.INDIVIDUAL
    company_data: Optional[CompanyCreate] = None
    invite_code: Optional[str] = None

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

    @field_validator("accepted_terms")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("Terms and conditions must be accepted")
        return v

    @field_validator('company_data')
    def validate_company_data(cls, v, info):
        if info.data.get('company_relationship') == CompanyRelationship.NEW_COMPANY and not v:
            raise ValueError("Company data is required when creating a new company")
        return v

    @field_validator('invite_code')
    def validate_invite_code(cls, v, info):
        if info.data.get('company_relationship') == CompanyRelationship.JOIN_COMPANY and not v:
            raise ValueError("Invite code is required when joining a company")
        return v

# Enhanced User Response
class UserResponse(UserBase):
    id: int
    company_id: Optional[int] = None
    registered_at: datetime
    last_activity: Optional[datetime] = None
    is_active: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True, extra='forbid')

# Enhanced Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = True
    device_info: Optional[str] = None  # For device tracking

    model_config = ConfigDict(extra='forbid')

# Enhanced Token Response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    permissions: Optional[List[str]] = []
    
    model_config = ConfigDict(extra='forbid')

# Token Refresh
class TokenRefresh(BaseModel):
    refresh_token: str
    model_config = ConfigDict(extra='forbid')

# Password Reset
class PasswordReset(BaseModel):
    email: EmailStr
    model_config = ConfigDict(extra='forbid')

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str

    @field_validator("reset_token")
    def validate_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Invalid reset token")
        return v

    @field_validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

    model_config = ConfigDict(extra='forbid')

# Change Password
class ChangePassword(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

    model_config = ConfigDict(extra='forbid')

# Join Company Request
class JoinCompanyRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None
    invite_code: str
    accepted_terms: bool = False

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("accepted_terms")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("Terms and conditions must be accepted")
        return v

    @field_validator("invite_code")
    def validate_invite_code(cls, v):
        if not v or len(v) < 4:
            raise ValueError("Valid invite code is required")
        return v

# Security Event Logging
class SecurityEvent(BaseModel):
    event_type: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = datetime.utcnow()

# API Response Standards
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[List[str]] = None

class ValidationErrorResponse(BaseModel):
    success: bool = False
    message: str = "Validation error"
    errors: List[dict]
