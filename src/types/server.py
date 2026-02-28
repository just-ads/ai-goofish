"""
Server 相关类型定义
"""
from typing import Optional, Literal

from pydantic import BaseModel

from src.types.task import TaskResultSortBy


class GoofishState(BaseModel):
    content: str


class GoofishStartLoginRequest(BaseModel):
    timeout_seconds: Optional[int] = 180


class GoofishSessionRequest(BaseModel):
    session_id: str


class GoofishSmsCodeRequest(BaseModel):
    session_id: str
    phone: str


class GoofishLoginRequest(BaseModel):
    session_id: str
    login_type: Literal['qr', 'password', 'sms']
    username: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    code: Optional[str] = None

class PaginationOptions(BaseModel):
    page: Optional[int] = 1
    limit: Optional[int]
    recommended_only: Optional[bool]
    sort_by: Optional[TaskResultSortBy]
    order: Optional[Literal['asce', 'desc']]
