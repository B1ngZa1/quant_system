"""用户数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, PaginationParams


class UserBase(BaseSchema):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """用户创建"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseSchema):
    """用户更新"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = None
    preferences: Optional[dict] = None


class UserPasswordUpdate(BaseSchema):
    """密码更新"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)


class UserInDB(UserBase):
    """数据库中的用户"""
    id: int
    is_active: bool
    is_verified: bool
    avatar: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserResponse(UserInDB):
    """用户响应"""
    pass


class UserLogin(BaseSchema):
    """用户登录"""
    username: str
    password: str


class Token(BaseSchema):
    """令牌"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseSchema):
    """令牌载荷"""
    sub: Optional[int] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class UserListParams(PaginationParams):
    """用户列表参数"""
    search: Optional[str] = None
    is_active: Optional[bool] = None
