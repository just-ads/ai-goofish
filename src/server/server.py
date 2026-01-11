import hashlib
import os
import secrets
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.api.router import api_router
from src.env import SECRET_KEY_FILE, SERVER_PORT, WEB_PASSWORD
from src.server.scheduler import initialize_task_scheduler, shutdown_task_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Web服务器正在启动，正在加载所有任务...")
    await initialize_task_scheduler()

    yield

    print("Web服务器正在关闭，正在终止所有爬虫进程...")
    shutdown_task_scheduler()


def load_or_create_secret_key():
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        key = secrets.token_urlsafe(50)
        with open(SECRET_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key)
        return key


# 计算密码的MD5值（与原始逻辑一致）
WEB_PASSWORD_MD5 = hashlib.md5(WEB_PASSWORD.encode('utf-8')).hexdigest()

# 创建FastAPI应用
app = FastAPI(title="闲鱼智能监控机器人", lifespan=lifespan)

# 挂载静态文件
app.mount('/static', StaticFiles(directory='resources/static'), name='static')

# 注册API路由
app.include_router(api_router)


# ----------------- 前端路由 -----------------
@app.get("/{path:path}")
async def index(request: Request, path: str):
    is_html_request = "text/html" in request.headers.get("accept", "").lower()

    if is_html_request:
        return FileResponse("resources/index.html")

    raise HTTPException(status_code=404)


def start_server():
    print(f"启动 Web 管理界面，请在浏览器访问 http://127.0.0.1:{SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)


if __name__ == "__main__":
    start_server()