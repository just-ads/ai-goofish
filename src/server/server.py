import asyncio
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from json import JSONDecodeError
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette.responses import HTMLResponse, FileResponse
from starlette.staticfiles import StaticFiles

from src.agent.client import AiClient
from src.config import WEB_USERNAME, WEB_PASSWORD, SERVER_PORT, STATE_FILE, SECRET_KEY_FILE, get_envs, set_envs
from src.server.scheduler import initialize_task_scheduler, shutdown_task_scheduler, add_task_to_scheduler, update_scheduled_task, run_task, remove_task_from_scheduler, \
    is_task_running, get_all_running_tasks, stop_task
from src.task.result import get_task_result, remove_task_result, get_product_prices
from src.task.task import get_all_tasks, add_task, update_task, get_task, remove_task, TaskUpdate, TaskWithoutID


class GoofishState(BaseModel):
    content: str


class PaginationOptions(BaseModel):
    page: Optional[int] = 1
    limit: Optional[int] = 20
    recommended_only: Optional[bool] = False
    sort_by: Optional[str] = "publish_time"
    order: Optional[str] = "asce"


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


# --------------- 登录 -------------------
@app.post("/api/login", response_model=dict)
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
            task['running'] = is_task_running(task.get('task_id'))
        return success_response("任务获取成功", tasks)
    except Exception:
        raise HTTPException(status_code=500, detail="读取任务配置时发生错误")


@app.post("/api/tasks/create", response_model=dict, dependencies=[Depends(verify_token)])
async def api_create_task(req: TaskWithoutID):
    try:
        task = await add_task(req)
        if task.get('enabled'):
            add_task_to_scheduler(task)
        return success_response("任务创建成功", task)
    except Exception:
        raise HTTPException(status_code=500, detail="创建失败")


@app.post("/api/tasks/update", response_model=dict, dependencies=[Depends(verify_token)])
async def api_update_task(req: TaskUpdate):
    try:
        old_task = await get_task(req.task_id)
        new_task = await update_task(req)

        if new_task.get('enabled'):
            # 如果任务之前是禁用状态，现在启用了，添加到调度器
            if not old_task.get('enabled'):
                add_task_to_scheduler(new_task)
            else:
                # 如果任务之前就是启用的，更新调度器中的任务
                await update_scheduled_task(new_task)
        else:
            # 如果任务被禁用，从调度器中移除
            remove_task_from_scheduler(req.task_id)

        return success_response("任务更新成功", new_task)
    except Exception as e:
        print(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail="更新任务失败")


@app.delete("/api/tasks/delete/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_remove_task(task_id: int):
    try:
        remove_task_from_scheduler(task_id)
        await remove_task(task_id)
        return success_response("任务删除成功")
    except Exception:
        raise HTTPException(status_code=500, detail="更新删除失败")


@app.post("/api/tasks/run/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_run_task(task_id: int):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        if is_task_running(task_id):
            return success_response("任务已在运行中", {"task_id": task_id, "running": True})

        asyncio.create_task(run_task(task['task_id'], task['task_name']))

        return success_response("任务启动中", {"task_id": task_id, "running": True})
    except Exception:
        raise HTTPException(status_code=500, detail="任务运行失败")


@app.post('/api/tasks/stop/{task_id}', response_model=dict, dependencies=[Depends(verify_token)])
async def api_stop_task(task_id: int):
    try:
        stop_task(task_id)
        return success_response("任务停止成功")
    except Exception:
        raise HTTPException(status_code=500, detail="任务停止失败")


@app.get('/api/tasks/status', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_tasks_status():
    try:
        data = get_all_running_tasks()
        return success_response('请求成功', data)
    except Exception:
        raise HTTPException(status_code=500, detail="任务状态检测失败")


@app.get('/api/tasks/status/{task_id}', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_task_status(task_id: int):
    try:
        running = is_task_running(task_id)
        return success_response("任务状态检测", {"running": running})
    except Exception:
        raise HTTPException(status_code=500, detail="任务状态检测失败")


@app.post("/api/results/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_task_results(task_id: int, data: PaginationOptions):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")
        result = await get_task_result(task['keyword'], data.page, data.limit, data.recommended_only, data.sort_by, data.order)
        return success_response("结果获取成功", result)
    except Exception:
        raise HTTPException(status_code=500, detail="结果获取失败")


@app.delete("/api/results/{task_id}", response_model=dict, dependencies=[Depends(verify_token)])
async def api_remove_task_results(task_id: int):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")
        remove_task_result(task.get('keyword'))
        return success_response("删除成功")
    except Exception:
        raise HTTPException(status_code=500, detail="删除失败")


@app.get('/api/results/prices/{task_id}', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_task_prices(task_id: int):
    try:
        task = await get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")
        prices = await get_product_prices(task['keyword'])
        return success_response('获取成功', prices)
    except Exception:
        raise HTTPException(status_code=500, detail="获取失败")


# --------------- goofish 相关 ----------------
@app.post("/api/goofish/state/save", response_model=dict, dependencies=[Depends(verify_token)])
async def api_save_goofish_state(data: GoofishState):
    try:
        json.loads(data.content)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            f.write(data.content)
        return success_response("保存成功")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式")
    except Exception:
        raise HTTPException(status_code=500, detail="保存失败")


@app.delete("/api/goofish/state/delete", response_model=dict, dependencies=[Depends(verify_token)])
async def api_delete_goofish_state():
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            return success_response("删除成功")
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except Exception:
        raise HTTPException(status_code=500, detail="删除失败")


@app.get('/api/goofish/status', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_goofish_status():
    return success_response("状态获取成功", os.path.exists(STATE_FILE))


@app.get('/api/system', response_model=dict, dependencies=[Depends(verify_token)])
async def api_get_system():
    return success_response('获取成功', get_envs())


@app.post('/api/system', response_model=dict, dependencies=[Depends(verify_token)])
async def api_save_system(envs: dict):
    try:
        set_envs(envs)
        return success_response('保存成功', get_envs())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")


@app.post('/api/system/aitest', response_model=dict, dependencies=[Depends(verify_token)])
async def api_aitest(config: dict):
    try:
        extra_body = config.get('OPENAI_EXTRA_BODY')
        client = AiClient(
            base_url=config.get('OPENAI_BASE_URL'),
            api_key=config.get('OPENAI_API_KEY'),
            model_name=config.get('OPENAI_MODEL_NAME'),
            proxy=config.get('OPENAI_PROXY_URL'),
            extra_body=json.loads(extra_body) if extra_body else None
        )
        messages = await client.ask(
            [{"role": "user", "content": "Hello."}],
            'text'
        )
        return success_response('测试成功', f'{messages}')
    except JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"OPENAI_EXTRA_BODY: 无效JSON字符串")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {e}")


# ----------------- 路由 -----------------
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
