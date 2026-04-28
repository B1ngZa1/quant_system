"""基础数据模型"""
from datetime import datetime
from typing import List, Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础模式类"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class ResponseBase(BaseSchema):
    """响应基础类"""
    code: int = 200
    message: str = "success"


class DataResponse(ResponseBase, Generic[T]):
    """数据响应类"""
    data: T


class ListResponse(ResponseBase, Generic[T]):
    """列表响应类"""
    data: List[T]
    total: int = 0
    page: int = 1
    page_size: int = 20


class PaginationParams(BaseSchema):
    """分页参数"""
    page: int = 1
    page_size: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class IDResponse(ResponseBase):
    """ID响应"""
    id: int


class SuccessResponse(ResponseBase):
    """成功响应"""
    success: bool = True
