from pydantic import BaseModel, EmailStr, Field
from src.domain.models import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address for the account")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Role of the user (ADMIN, CUSTOMER)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "customer@shopsphere.ai",
                "password": "SuperSecretPassword123",
                "full_name": "Jane Doe",
                "role": "CUSTOMER"
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(..., description="Account password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "customer@shopsphere.ai",
                "password": "SuperSecretPassword123"
            }
        }
    }


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Access token to authorize future requests")
    refresh_token: str = Field(..., description="Refresh token used to obtain a new access token")
    token_type: str = Field("bearer", description="Token authentication scheme")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token issued during login or last rotation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }
