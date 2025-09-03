import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from starlette.responses import HTMLResponse, FileResponse
from starlette.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from src.config import WEB_USERNAME, WEB_PASSWORD, SERVER_PORT
from src.server.scheduler import load_all_tasks, stop_all_tasks, start_task, update_task_job, run_task, stop_task
from src.task.result import get_task_result
from src.task.task import get_all_tasks, add_task, Task, update_task, get_task


class TaskRequest(BaseModel):
    task_name: str
    keyword: str
    description: str
    personal_only: bool = True
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    max_pages: int = 3
    cron: Optional[str] = None


async def lifespan(app: FastAPI):
    print("Web服务器正在启动，正在加载所有任务...")
    await load_all_tasks()

    yield

    print("Web服务器正在关闭，正在终止所有爬虫进程...")
    stop_all_tasks()


app = FastAPI(title="闲鱼智能监控机器人", lifespan=lifespan)
app.mount('/static', StaticFiles(directory='resources/static'), name='static')

WEB_PASSWORD_MD5 = hashlib.md5(WEB_PASSWORD.encode('utf-8')).hexdigest()
SECRET_KEY = secrets.token_urlsafe(50)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ----------------- 统一返回工具 -----------------
def success_response(message: str, data=None):
    return {"message": message, "data": data}


# ----------------- JWT 工具函数 -----------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != WEB_USERNAME:
            raise HTTPException(status_code=401, detail="无效的 Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="认证失败")


# ----------------- 路由 -----------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("resources/static/index.html")


# --------------- 登录 -------------------
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != WEB_USERNAME or form_data.password != WEB_PASSWORD_MD5:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": WEB_USERNAME},
        expires_delta=access_token_expires
    )
    return success_response("登录成功", {"access_token": access_token})


# --------------- 任务相关 ----------------
@app.get("/api/tasks", dependencies=[Depends(verify_token)])
async def api_get_tasks():
    try:
        tasks = await get_all_tasks()
        return success_response("任务获取成功", tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取任务配置时发生错误: {e}")


@app.post("/api/tasks/create", response_model=dict, dependencies=[Depends(verify_token)])
async def api_create_task(req: TaskRequest):
    try:
        new_task = {
            "task_name": req.task_name,
            "enabled": True,
            "keyword": req.keyword,
            "max_pages": req.max_pages,
            "personal_only": req.personal_only,
            "min_price": req.min_price,
            "max_price": req.max_price,
            "cron": req.cron,
            "description": req.description,
        }
        task_id = await add_task(new_task)
        start_task(new_task)  # 保持同步调用
        new_task_with_id = new_task.copy()
        new_task_with_id["task_id"] = task_id
        return success_response("任务创建成功", new_task_with_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败 {e}")


@app.post("/api/tasks/update", response_model=dict, dependencies=[Depends(verify_token)])
async def api_update_task(req: TaskRequest):
    try:
        new_task = await update_task(req)
        await update_task_job(new_task)
        return success_response("任务更新成功", new_task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务失败: {e}")


@app.post("/api/tasks/start/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_start_task(task_id: int):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")
        await run_task(task['task_id'], task['task_name'])
        return success_response("任务运行成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务运行失败: {e}")


@app.post("/api/tasks/stop/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_stop_task(task_id: int):
    try:
        stop_task(task_id)
        return success_response("任务停止成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务停止失败: {e}")


@app.get("/api/results/{task_id}", dependencies=[Depends(verify_token)])
async def api_get_task_results(task_id: int, page: int = 1, limit: int = 20, recommended_only: bool = False, sort_by: str = 'crawl_time'):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")
        result = await get_task_result(task['keyword'], page, limit, recommended_only, sort_by)
        return success_response("结果获取成功", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"结果获取失败: {e}")


# --------------- 状态相关 ----------------
@app.get('/api/status/goofish', dependencies=[Depends(verify_token)])
async def api_get_goofish_status():
    return success_response("状态获取成功", os.path.exists("xianyu_state.json"))


def start_sever():
    print(f"启动 Web 管理界面，请在浏览器访问 http://127.0.0.1:{SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)


if __name__ == "__main__":
    start_sever()
