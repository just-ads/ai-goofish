import asyncio
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette.responses import HTMLResponse, FileResponse
from starlette.staticfiles import StaticFiles

from src.config import WEB_USERNAME, WEB_PASSWORD, SERVER_PORT, STATE_FILE, SECRET_KEY_FILE
from src.server.scheduler import load_all_tasks, stop_all_tasks, schedule_task, reschedule_task, run_task, stop_task, is_running, get_all_running
from src.task.result import get_task_result
from src.task.task import get_all_tasks, add_task, update_task, get_task, remove_task, TaskUpdate, TaskWithoutID


class GoofishState(BaseModel):
    content: str


async def lifespan(app: FastAPI):
    print("Web服务器正在启动，正在加载所有任务...")
    await load_all_tasks()

    yield

    print("Web服务器正在关闭，正在终止所有爬虫进程...")
    stop_all_tasks()


def load_or_create_secret_key():
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        key = secrets.token_urlsafe(50)
        with open(SECRET_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key)
        return key


app = FastAPI(title="闲鱼智能监控机器人", lifespan=lifespan)
app.mount('/static', StaticFiles(directory='resources/static'), name='static')

WEB_PASSWORD_MD5 = hashlib.md5(WEB_PASSWORD.encode('utf-8')).hexdigest()
SECRET_KEY = load_or_create_secret_key()
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
@app.get("/api/tasks", response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_tasks():
    try:
        tasks = await get_all_tasks()
        for task in tasks:
            task['running'] = is_running(task.get('task_id'))
        return success_response("任务获取成功", tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取任务配置时发生错误: {e}")


@app.post("/api/tasks/create", response_model=dict, dependencies=[Depends(verify_token)])
async def api_create_task(req: TaskWithoutID):
    try:
        task = await add_task(req)
        schedule_task(task)
        return success_response("任务创建成功", task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败 {e}")


@app.delete("/api/tasks/delete/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_delete_task(task_id: int):
    try:
        task = await remove_task(task_id)
        if task:
            return success_response("任务删除成功")
        else:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {e}")


@app.post("/api/tasks/update", response_model=dict, dependencies=[Depends(verify_token)])
async def api_update_task(req: TaskUpdate):
    try:
        new_task = await update_task(req)
        await reschedule_task(new_task)
        return success_response("任务更新成功", new_task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务失败: {e}")


@app.post("/api/tasks/run/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_run_task(task_id: int):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")

        if is_running(task_id):
            return success_response("任务已在运行中", {"task_id": task_id, "running": True})

        asyncio.create_task(run_task(task['task_id'], task['task_name']))

        return success_response("任务启动中", {"task_id": task_id, "running": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务运行失败: {e}")


@app.post("/api/tasks/stop/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_stop_task(task_id: int):
    try:
        stop_task(task_id)
        return success_response("任务停止成功", {"task_id": task_id, "running": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务停止失败: {e}")


@app.get('/api/tasks/status', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_tasks_status():
    try:
        data = get_all_running()
        return success_response('请求成功', data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务状态检测失败: {e}")


@app.get('/api/tasks/status/{task_id}', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_task_status(task_id: int):
    try:
        running = is_running(task_id)
        return success_response("任务状态检测", {"running": running})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务状态检测失败: {e}")


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


# --------------- goofish 相关 ----------------
@app.post("/api/goofish/state/save", dependencies=[Depends(verify_token)])
async def api_save_goofish_state(data: GoofishState):
    try:
        json.loads(data.content)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            f.write(data.content)
        return success_response("保存成功")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败 {e}")


@app.delete("/api/goofish/state/delete", dependencies=[Depends(verify_token)])
async def api_delete_goofish_state():
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            return success_response("删除成功")
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败 {e}")


@app.get('/api/goofish/status', dependencies=[Depends(verify_token)])
async def api_get_goofish_status():
    return success_response("状态获取成功", os.path.exists(STATE_FILE))


def start_server():
    print(f"启动 Web 管理界面，请在浏览器访问 http://127.0.0.1:{SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)


if __name__ == "__main__":
    start_server()
