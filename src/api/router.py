"""
主路由器模块
整合所有API路由模块
"""
from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.tasks import router as tasks_router
from src.api.results import router as results_router
from src.api.goofish import router as goofish_router
from src.api.system import router as system_router
from src.api.providers import router as providers_router
from src.api.notify import router as notify_router

# 创建主路由器
api_router = APIRouter(prefix="/api")

# 注册所有子路由
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(results_router)
api_router.include_router(goofish_router)
api_router.include_router(system_router)
api_router.include_router(providers_router)
api_router.include_router(notify_router)