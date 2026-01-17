# 闲鱼监控机器人 (AI Goofish)

基于 `Playwright + FastAPI` 的闲鱼商品监控与采集系统，支持多任务调度、Web 管理界面、结果存储与查询，可选接入 AI 评估与多种通知方式。

------------------------------------------------------------------------

## 🖼️ 页面截图

### 1. 登录

<img width="1189" height="908" alt="image" src="https://github.com/user-attachments/assets/00df6b62-771a-4caa-8201-fa95ccc5153f" />

### 2. 主页

<img width="1189" height="894" alt="image" src="https://github.com/user-attachments/assets/31ab2ac3-ea93-44cc-b7e4-f20f0ac91422" />

------------------------------------------------------------------------

## 📂 项目结构

```
./
├── src/                  # Python 后端（API/调度/爬虫/AI/通知）
├── webui/                # Vue 3 前端（子模块），构建输出到 ../resources/
├── resources/            # 前端构建产物（resources/index.html + resources/static/*）
├── tests/                # Python unittest
├── jsonl/                # 采集结果（*.jsonl，一行一个 JSON）
├── tasks.json            # 任务配置（JSON 数组）
├── app.config            # 系统配置（JSON，默认文件名）
├── ai.config             # AI 配置（JSON 数组）
├── notifier.config       # 通知配置（JSON 数组）
├── goofish_state.json    # Playwright storage_state（cookies/session）
├── secret_key.txt        # JWT secret（自动生成/读取）
├── start.py              # 后端启动入口
├── start_spider.py       # 爬虫入口（按 task_id 运行）
├── dev.py                # 一键开发（前后端一起）
└── docker-compose.yml    # Docker Compose
```

说明：`webui/` 是子模块。首次拉取建议使用 `--recurse-submodules`，或执行 `git submodule update --init --recursive`。

------------------------------------------------------------------------

## ✨ 功能列表

- [x] 多任务并行监控与定时调度（APScheduler + 随机偏移）
- [x] 支持关键词、页数、价格区间、个人闲置等筛选条件
- [x] 采集商品信息与卖家资料
- [x] FastAPI 提供任务/结果/系统/AI/通知配置等管理接口
- [x] Web 管理界面：任务管理、运行状态、结果查看
- [x] 可选 AI 商品评估（通过 `ai.config` 配置 AI Provider）
- [x] 通知：ntfy / gotify / 企业微信 webhook（配置存储在 `notifier.config`）
- [x] Docker 一键部署

------------------------------------------------------------------------

## ⚡ 快速开始

更完整的一键开发说明见 `QUICKSTART.md`。

### Docker 部署

1) 拉取代码（包含子模块）

```bash
git clone --recurse-submodules https://github.com/just-ads/ai-goofish.git
cd ai-goofish
```

2) （可选）创建 `.env`

```bash
cp .env.example .env
```

3) 启动

```bash
docker compose up --build -d
```

访问：`http://127.0.0.1:8000`

### 本地开发（推荐）

使用一键脚本启动前后端开发服务器：

```bash
python dev.py
```

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

### 手动启动（后端/前端分开）

1) 安装后端依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
playwright install
```

2) 启动后端

```bash
python start.py
```

3) 前端开发

```bash
cd webui
npm install
npm run dev
```

4) 构建前端到 `resources/`

```bash
cd webui
npm run build
```

------------------------------------------------------------------------

## ⚙️ 配置说明

本项目同时使用“环境变量（.env）”和“JSON 配置文件（*.config）”。

### 1) 环境变量（`.env`）

示例见 `.env.example`，主要用于基础服务配置：

- `SERVER_PORT`：服务端口（默认 8000）
- `WEB_USERNAME` / `WEB_PASSWORD`：Web 登录用户名/密码（默认 admin/admin）

注意：前端登录时会对密码做 MD5（服务端按同样逻辑校验），生产环境务必修改默认密码。

### 2) 系统配置（`app.config`）

后端读取/写入的默认系统配置文件是 `app.config`（JSON）。可用示例：

```bash
cp config.example.json app.config
```

对应 API：`/api/system`。

### 3) AI 配置（`ai.config`）

AI Provider 配置存储在 `ai.config`（JSON 数组）。可用示例：

```bash
cp ai.example.json ai.config
```

对应 API：`/api/ai`。

### 4) 通知配置（`notifier.config`）

通知配置存储在 `notifier.config`（JSON 数组），通常通过 Web 管理界面创建/更新。

对应 API：`/api/notifier`。

------------------------------------------------------------------------

## 🧪 测试

```bash
python -m unittest discover tests/
```

------------------------------------------------------------------------

## 🔐 安全与仓库卫生（重要）

以下文件/目录通常包含运行时数据或敏感信息，不建议提交到版本库：

- `.env`
- `app.config` / `ai.config` / `notifier.config`
- `secret_key.txt`
- `goofish_state.json`

------------------------------------------------------------------------

## 💖 鸣谢

- [ai-goofish-monitor](https://github.com/dingyufei615/ai-goofish-monitor)

------------------------------------------------------------------------

# 免责声明

本系统/平台/软件（以下简称“本服务”）所提供的内容、资料及相关信息，仅供参考与学习使用。使用者在使用本服务时，应自行判断其适用性与风险。

## 1. 内容准确性

本服务尽力确保所提供的信息完整、准确，但不对其及时性、可靠性或适用性作出任何保证。使用者应在依赖前进行独立验证。

## 2. 责任限制

因使用或无法使用本服务所导致的任何直接或间接损失、数据丢失、系统故障或其他后果，本服务提供方均不承担任何责任。

## 3. 第三方链接或资源

本服务可能包含第三方提供的链接、接口或资源，本服务对其内容或使用结果不作任何保证或承诺。

## 4. 法律遵循

使用者在使用本服务时，应遵守所在地相关法律法规，若因使用不当而违反法律规定，责任由使用者自行承担。

## 5. 免责声明的变更

本服务有权随时修改或更新本免责声明，修改后的内容一经公布即刻生效。
