"""
认证相关路由模块
处理登录、JWT认证等功能
"""
import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from src.env import WEB_USERNAME, WEB_PASSWORD, SECRET_KEY_FILE
from src.config import get_config_instance
import os
import secrets

# 创建路由器
router = APIRouter(prefix="/auth", tags=["authentication"])

# 加载或创建密钥
def load_or_create_secret_key():
    """加载或创建JWT密钥"""
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        key = secrets.token_urlsafe(50)
        with open(SECRET_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key)
        return key

# 全局常量
SECRET_KEY = load_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ----------------- JWT 工具函数 -----------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_token(token: str = Depends(oauth2_scheme)):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != WEB_USERNAME:
            raise HTTPException(status_code=401, detail="无效的 Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="认证失败")


# ----------------- 统一返回工具 -----------------
def success_response(message: str, data=None):
    """统一成功响应格式"""
    return {"message": message, "data": data}


# ----------------- 登录接口 -----------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录接口"""
    config = get_config_instance()
    config_data = config.get_config()
    
    # 从配置中获取用户名和密码
    web_username = config_data.get("server", {}).get("web_username", WEB_USERNAME)
    web_password = config_data.get("server", {}).get("web_password", WEB_PASSWORD)
    
    # 计算密码的MD5值（与原始server.py一致）
    web_password_md5 = hashlib.md5(web_password.encode('utf-8')).hexdigest()
    
    if form_data.username != web_username or form_data.password != web_password_md5:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": web_username},
        expires_delta=access_token_expires
    )
    return success_response("登录成功", {"access_token": access_token})