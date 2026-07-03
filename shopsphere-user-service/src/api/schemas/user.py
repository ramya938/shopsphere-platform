import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from src.domain.models import UserRole

class UserResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the user")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="Assigned role of the user")
    is_active: bool = Field(..., description="Status flag indicating if the account is active")
    created_at: datetime = Field(..., description="Timestamp when the user account was created")
    updated_at: datetime = Field(..., description="Timestamp when the user account was last updated")

    model_config = {
        "from_attributes": True, # Pydantic v2 equivalent of orm_mode=True
        "json_schema_extra": {
            "example": {
                "id": "a9b8c7d6-e5f4-3c2b-1a09-876543210fed",
                "email": "customer@shopsphere.ai",
                "full_name": "Jane Doe",
                "role": "CUSTOMER",
                "is_active": True,
                "created_at": "2026-06-22T12:00:00Z",
                "updated_at": "2026-06-22T12:00:00Z"
            }
        }
    }


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = Field(default=None, description="New email address")
    full_name: str | None = Field(default=None, min_length=2, max_length=100, description="New full name")
    password: str | None = Field(default=None, min_length=8, max_length=128, description="New password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "jane.new@shopsphere.ai",
                "full_name": "Jane Smith",
                "password": "NewSecretPassword123"
            }
        }
    }
