from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """通用API响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    requestId: Optional[str] = Field(default=None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    hasNext: bool = Field(description="是否有下一页")
    hasPrev: bool = Field(description="是否有上一页")


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
    request_id: Optional[str] = None
) -> JSONResponse:
    """创建成功响应"""
    response_data = ApiResponse(
        code=code,
        message=message,
        data=data,
        requestId=request_id
    )
    
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response_data.dict())
    )


def error_response(
    message: str,
    code: int = 500,
    data: Any = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """创建错误响应"""
    response_data = ApiResponse(
        code=code,
        message=message,
        data=data,
        requestId=request_id
    )
    
    return JSONResponse(
        status_code=code if code < 500 else 500,
        content=jsonable_encoder(response_data.dict())
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    size: int,
    message: str = "success",
    request_id: Optional[str] = None
) -> JSONResponse:
    """创建分页响应"""
    pages = (total + size - 1) // size  # 向上取整
    
    paginated_data = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
        hasNext=page < pages,
        hasPrev=page > 1
    )
    
    return success_response(
        data=paginated_data.dict(),
        message=message,
        request_id=request_id
    )


# 字段名称转换工具
def snake_to_camel(snake_str: str) -> str:
    """将snake_case转换为camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """将camelCase转换为snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_keys_to_camel(data: Any) -> Any:
    """递归转换字典键名为camelCase"""
    if isinstance(data, dict):
        return {snake_to_camel(k): convert_keys_to_camel(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_camel(item) for item in data]
    else:
        return data


def convert_keys_to_snake(data: Any) -> Any:
    """递归转换字典键名为snake_case"""
    if isinstance(data, dict):
        return {camel_to_snake(k): convert_keys_to_snake(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake(item) for item in data]
    else:
        return data