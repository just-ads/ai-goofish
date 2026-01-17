# 快速开始

使用以下脚本一键启动前端和后端开发服务器。

## 🚀 快速启动脚本

### Python 跨平台脚本（推荐）
```bash
python dev.py
```

**优点：**
- ✅ 跨平台支持（Windows/Linux/macOS）
- ✅ 自动检查和安装依赖
- ✅ 统一管理前后端进程
- ✅ Ctrl-C 一键停止所有服务
- ✅ 彩色输出，清晰的状态提示

### Windows 批处理脚本
```bash
dev.bat
```

**特点：**
- 🪟 在两个独立窗口中运行
- 📦 自动安装缺失的依赖
- 🎯 双击即可启动

### Linux/macOS Shell 脚本
```bash
./dev.sh
```

**特点：**
- 🐧 后台运行前后端服务
- 📦 自动安装缺失的依赖
- 🛑 Ctrl-C 优雅停止所有服务

## 📋 脚本功能

### 依赖检查
脚本会自动检查以下依赖：
- ✅ Python 虚拟环境（.venv 或 venv）
- ✅ 后端 Python 依赖（requirements.txt）
- ✅ 前端 Node.js 依赖（node_modules）

### 自动安装
如果检测到依赖缺失，脚本会自动：
- 创建 Python 虚拟环境
- 安装后端依赖包
- 安装前端 npm 包

### 启动服务
- 🔧 后端：FastAPI 服务器（http://127.0.0.1:8000）
- 🎨 前端：Vite 开发服务器（http://127.0.0.1:5173）

## 📌 访问地址

启动成功后，可以通过以下地址访问：

- **后端 API**: http://127.0.0.1:8000
- **前端界面**: http://127.0.0.1:5173
- **API 文档**: http://127.0.0.1:8000/docs

默认登录凭据：
- 用户名：`admin`
- 密码：`admin`

⚠️ **注意**：生产环境请务必修改 `config.json` 中的默认密码！

## 💡 使用技巧

### 首次使用
首次运行脚本会自动安装依赖，可能需要几分钟：
```bash
python dev.py
# 首次运行会自动：
# 1. 创建 Python 虚拟环境
# 2. 安装后端依赖
# 3. 安装前端依赖
# 4. 启动前后端服务
```

### 停止服务
- **Python 脚本**：按 `Ctrl+C` 停止所有服务
- **Windows 脚本**：关闭对应窗口即可停止服务
- **Linux/macOS 脚本**：按 `Ctrl+C` 停止所有服务

### 只启动前端或后端
如果需要单独启动某个服务：

```bash
# 只启动后端
python start.py

# 只启动前端
cd webui
npm run dev
```

### 手动安装依赖
如果需要手动安装依赖：

```bash
# 后端
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
playwright install

# 前端
cd webui
npm install
```

## 🔧 故障排除

### Python 虚拟环境问题
如果遇到虚拟环境问题，尝试删除后重新创建：
```bash
# Windows
rmdir /s .venv
# Linux/macOS
rm -rf .venv
python dev.py  # 会自动重新创建
```

### 端口冲突
如果端口被占用，修改以下配置：
- 后端端口：`config.json` 中的 `server.port`
- 前端端口：`webui/vite.config.ts` 中的 `server.port`

### 依赖安装失败
如果依赖安装失败，尝试使用国内镜像：

```bash
# 后端使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 前端使用淘宝镜像
cd webui
npm install --registry=https://registry.npmmirror.com
```

## 📝 相关文件

- `dev.py` - Python 跨平台启动脚本（推荐）
- `dev.bat` - Windows 批处理脚本
- `dev.sh` - Linux/macOS Shell 脚本
- `AGENTS.md` - 项目开发指南

## 🆘 获取帮助

如遇到问题，请参考：
- 项目 README.md
- AGENTS.md 开发指南
- FastAPI 文档：http://127.0.0.1:8000/docs
