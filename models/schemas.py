from pydantic import BaseModel, Field, field_validator
import re

# password should be minimum 8 characters, at least one uppercase letter, one number and one special character
class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8)
    email: str = Field(...)
    role: str = Field('user')

    @field_validator('password')
    def password_strength(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]', v):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character.')
        return v

    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores.')
        return v

    @field_validator('email')
    def valid_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            raise ValueError('Invalid email address.')
        return v

    @field_validator('role')
    def valid_role(cls, v):
        if v not in ('user', 'admin'):
            raise ValueError("Role must be 'user' or 'admin'.")
        return v

class InventoryItemSchema(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., ge=0)
    unit_price: float = Field(..., ge=0.0)
    