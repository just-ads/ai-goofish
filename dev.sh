#!/bin/bash
# AI Goofish 开发环境启动脚本 (Linux/macOS)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo "==================================================="
    echo "  AI Goofish 开发环境启动器"
    echo "==================================================="
    echo ""
}

check_backend_deps() {
    # 检查虚拟环境
    if [ ! -f ".venv/bin/python" ] && [ ! -f "venv/bin/python" ]; then
        echo -e "${RED}❌ Python 虚拟环境不存在${NC}"
        echo -e "${YELLOW}📦 正在创建虚拟环境并安装依赖...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    else
        echo -e "${GREEN}✅ Python 虚拟环境已存在${NC}"
    fi
}

check_frontend_deps() {
    # 检查前端依赖
    if [ ! -d "webui/node_modules" ]; then
        echo -e "${RED}❌ 前端依赖未安装${NC}"
        echo -e "${YELLOW}📦 正在安装前端依赖...${NC}"
        cd webui
        npm install
        cd ..
    else
        echo -e "${GREEN}✅ 前端依赖已安装${NC}"
    fi
}

start_services() {
    print_header
    echo -e "${YELLOW}📋 检查依赖...${NC}"
    check_backend_deps
    check_frontend_deps

    echo ""
    echo -e "${YELLOW}🚀 启动服务...${NC}"
    echo ""

    # 启动后端
    echo -e "${GREEN}[后端]${NC} 启动 FastAPI 服务器..."
    if [ -f ".venv/bin/python" ]; then
        source .venv/bin/activate
        set DEV=1
        set DEBUG=1
        python start.py &
        BACKEND_PID=$!
    elif [ -f "venv/bin/python" ]; then
        source venv/bin/activate
        set DEV=1
        set DEBUG=1
        python start.py &
        BACKEND_PID=$!
    fi

    # 启动前端
    echo -e "${GREEN}[前端]${NC} 启动 Vite 开发服务器..."
    cd webui
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    # 等待一秒让服务启动
    sleep 2

    echo ""
    echo "==================================================="
    echo -e "${GREEN}✅ 开发环境已启动！${NC}"
    echo "==================================================="
    echo ""
    echo "📌 服务地址："
    echo "  • 后端 API: http://127.0.0.1:8000"
    echo "  • 前端界面: http://127.0.0.1:5173"
    echo "  • API 文档: http://127.0.0.1:8000/docs"
    echo ""
    echo -e "${YELLOW}💡 提示：按 Ctrl+C 停止所有服务${NC}"
    echo "==================================================="
    echo ""

    # 捕获退出信号
    trap cleanup SIGINT SIGTERM

    # 等待进程
    wait $BACKEND_PID $FRONTEND_PID
}

cleanup() {
    echo ""
    echo ""
    echo -e "${YELLOW}🛑 正在停止服务...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "  停止后端 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "  停止前端 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    exit 0
}

# 运行
start_services
