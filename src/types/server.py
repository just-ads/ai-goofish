"""
Server 相关类型定义
"""
from typing import Optional, Literal

from pydantic import BaseModel

from src.types.task import TaskResultSortBy


class GoofishState(BaseModel):
    content: str

class PaginationOptions(BaseModel):
    page: Optional[int] = 1
    limit: Optional[int]
    recommended_only: Optional[bool]
    sort_by: Optional[TaskResultSortBy]
    order: Optional[Literal['asce', 'desc']]