@echo off
chcp 65001 >nul
title AI Goofish 开发环境

echo ===================================================
echo   AI Goofish 开发环境启动器
echo ===================================================
echo.

REM 检查后端虚拟环境
if not exist ".venv\Scripts\python.exe" if not exist "venv\Scripts\python.exe" (
    echo ❌ Python 虚拟环境不存在
    echo 📦 正在创建虚拟环境并安装依赖...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ Python 虚拟环境已存在
)

REM 检查前端依赖
if not exist "webui\node_modules\" (
    echo ❌ 前端依赖未安装
    echo 📦 正在安装前端依赖...
    cd webui
    call npm install
    cd ..
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ 前端依赖已安装
)

echo.
echo ===================================================
echo 🚀 启动服务...
echo ===================================================
echo.

REM 启动后端（新窗口）
echo [后端] 启动 FastAPI 服务器...
if exist ".venv\Scripts\python.exe" (
    start "AI Goofish Backend" cmd /k ".venv\Scripts\activate.bat && python start.py"
) else if exist "venv\Scripts\python.exe" (
    start "AI Goofish Backend" cmd /k "venv\Scripts\activate.bat && python start.py"
) else (
    echo ❌ 找不到 Python 虚拟环境
    pause
    exit /b 1
)

REM 启动前端（新窗口）
echo [前端] 启动 Vite 开发服务器...
cd webui
start "AI Goofish Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ===================================================
echo ✅ 开发环境已启动！
echo ===================================================
echo.
echo 📌 服务地址：
echo   • 后端 API: http://127.0.0.1:8000
echo   • 前端界面: http://127.0.0.1:5173
echo   • API 文档: http://127.0.0.1:8000/docs
echo.
echo 💡 提示：关闭窗口即可停止对应的服务
echo.
