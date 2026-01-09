# 闲鱼监控机器人 (Goofish Monitor)

一个基于 **Playwright + FastAPI**
的闲鱼商品智能监控与采集系统，支持多任务调度、Web
管理界面、结果存储与查询，适合批量监控目标商品并进行后续数据分析。

------------------------------------------------------------------------

## 🖼️ 页面截图

### 1. 登录

<img width="1189" height="908" alt="image" src="https://github.com/user-attachments/assets/00df6b62-771a-4caa-8201-fa95ccc5153f" />

### 2. 主页

<img width="1189" height="894" alt="image" src="https://github.com/user-attachments/assets/31ab2ac3-ea93-44cc-b7e4-f20f0ac91422" />

------------------------------------------------------------------------

## 📂 项目结构

    .
    ├── src/
    │   ├── config.py           # 全局配置管理（JSON配置文件）
    │   ├── agent/              # AI代理模块（v2.0+ 新架构）
    │   │   ├── client.py       # 通用Agent客户端
    │   │   ├── models.py       # Agent数据模型
    │   │   └── product_evaluator.py  # 商品评估器
    │   ├── spider/             # 页面解析逻辑
    │   │   ├── parsers.py      # 商品与卖家数据解析
    │   │   ├── spider.py       # 核心爬虫脚本，负责商品采集
    │   ├── task/
    │   │   ├── task.py         # 任务数据结构与管理
    │   │   ├── result.py       # 爬取结果存储与查询
    │   ├── server/
    │   │   ├── scheduler.py    # 任务调度与运行管理
    │   │   ├── server.py       # Web 服务入口，提供任务管理与结果接口
    │   ├── utils/
    │   │   ├── utils.py        # 工具函数
    ├── resources/
    │   └── static/             # 前端静态资源 (Web 管理界面)
    ├── config.example.json     # 配置文件示例
    ├── agents.example.json     # Agent配置示例
    └── test_agent_system.py    # Agent系统测试脚本

------------------------------------------------------------------------

## ✨ 功能列表

-   [x] 多任务并行监控
-   [x] 支持关键词、价格区间、个人闲置等筛选条件
-   [x] 采集商品信息与卖家完整资料
-   [x] 爬虫过程自动防反爬处理与休眠机制
-   [x] FastAPI 提供任务与结果管理接口
-   [x] Web 管理界面支持任务管理与结果查看
-   [x] 提供 **Docker 镜像**，一键部署
-   [x] 接入简单的 **AI 商品分析模块**
-   [x] 支持ntfy、geotify通知服务

------------------------------------------------------------------------

## 🚀 未来计划

-   [ ] 增加 **通知功能**（邮件/钉钉/微信推送）
-   [ ] 支持 **结果导出为 CSV/Excel**

-----------------------------------------------------------------------

## ⚡ 快速开始

### Docker 部署

#### 1. 环境准备

- [Docker Engine](https://docs.docker.com/engine/install/)

#### 2.拉取代码

```bash
git clone https://github.com/just-ads/ai-goofish.git
```

#### 3.创建.env 并运行容器

```bash
cd ai-goofish
# 创建.env
cp .env.example .env
# 构建并运行
docker compose up --build -d
```

### 本地开发

#### 1. 环境准备

- [Python 3.10+](https://www.python.org/downloads/)

安装依赖：

``` bash
pip install -r requirements.txt
playwright install
```

#### 2. 构建前端资源

```bash
cd webui
npm run build
```

#### 3. 启动服务

``` bash
python start.py
```

启动后访问(默认用户名admin，密码admin)：

    http://127.0.0.1:8000

登录后可在 Web 界面管理任务、启动/停止采集、查看数据。

------------------------------------------------------------------------

## ⚙️ 配置系统说明

### 新的配置方式（v2.0+）

从 v2.0 版本开始，AI Goofish 使用统一的 JSON 配置文件 (`config.json`) 来管理所有配置，**不再使用环境变量存储 AI 配置**。

#### 配置文件结构

项目根目录下的 `config.json` 文件包含所有配置：

```json
{
  "server": {
    "port": 8000,
    "host": "0.0.0.0",
    "debug": false,
    "secret_key": "随机生成的密钥",
    "web_username": "admin",
    "web_password": "admin"
  },
  "browser": {
    "headless": true,
    "channel": "chrome",
    "timeout": 30
  },
  "agents": {
    "enabled": true,
    "default_agent_id": "openai-gpt-4",
    "agents": [
      {
        "id": "openai-gpt-4",
        "name": "OpenAI GPT-4",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key": "你的API密钥",
        "model": "gpt-4",
        "headers": {
          "Authorization": "Bearer {{api_key}}",
          "Content-Type": "application/json"
        },
        "body_template": "{\"model\": \"{{model}}\", \"messages\": {{messages}}, \"temperature\": {{temperature}}}",
        "parameters": {
          "temperature": 0.2,
          "max_tokens": 2000
        },
        "enabled": true,
        "is_default": true
      }
    ]
  }
}
```

#### 快速开始

1. **复制示例配置**：
   ```bash
   cp config.example.json config.json
   ```

2. **编辑配置文件**：
   - 修改 `web_username` 和 `web_password`（建议修改）
   - 在 `agents.agents` 数组中配置你的 AI 服务
   - 设置 `agents.default_agent_id` 为你想使用的默认 Agent ID

3. **支持的 AI 服务**：
   - OpenAI (GPT-3.5, GPT-4)
   - Azure OpenAI
   - Anthropic Claude
   - DeepSeek
   - 阿里云通义千问
   - Google Gemini
   - 任何兼容 OpenAI API 格式的服务

#### 从旧版本迁移

如果你从 v1.x 升级到 v2.0：

1. 将环境变量中的 AI 配置迁移到 `config.json`
2. 删除 `.env` 文件中的 AI 相关环境变量
3. 运行测试脚本验证配置：`python test_agent_system.py`

#### 环境变量（仅限基础配置）

以下环境变量仍被支持，用于基础服务配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| SERVER_PORT | `8000` | Web 服务端口 |
| WEB_USERNAME | `admin` | Web 管理界面用户名 |
| WEB_PASSWORD | `admin` | Web 管理界面密码 |
| BROWSER_HEADLESS | `true` | Playwright 无头模式 |
| BROWSER_CHANNEL | `chrome` | 浏览器通道 |

**注意**：AI 相关配置（API密钥、模型等）现在必须通过 `config.json` 文件配置。

------------------------------------------------------------------------

## 🤖 Agent 系统架构（v2.0+）

### 设计理念

新的 Agent 系统采用 **通用化设计**，不关心具体的 AI 服务提供商。系统通过模板配置支持任何兼容的 AI API。

### 核心组件

1. **AgentConfig 模型** (`src/agent/models.py`)
   - 定义 Agent 的完整配置
   - 支持模板字符串渲染（使用 `{{variable}}` 语法）
   - 包含端点、API密钥、模型、请求头、请求体模板等

2. **AgentClient 客户端** (`src/agent/client.py`)
   - 通用 HTTP 客户端，不依赖特定 SDK
   - 支持模板渲染和参数替换
   - 内置重试机制和错误处理
   - 支持多种响应格式解析

3. **AgentManager 管理器** (`src/agent/client.py`)
   - 管理多个 Agent 配置
   - 提供默认 Agent 选择
   - 支持动态添加/删除 Agent

4. **ProductEvaluator 评估器** (`src/agent/product_evaluator.py`)
   - 商品分步骤评估逻辑
   - 使用新的 AgentClient 进行 AI 调用
   - 输出结构化评估结果

### 模板系统

Agent 系统使用模板字符串配置请求格式：

```json
{
  "headers": {
    "Authorization": "Bearer {{api_key}}",
    "Content-Type": "application/json"
  },
  "body_template": "{\"model\": \"{{model}}\", \"messages\": {{messages}}, \"temperature\": {{temperature}}}"
}
```

可用模板变量：
- `{{api_key}}`: API 密钥
- `{{model}}`: 模型名称
- `{{messages}}`: 消息列表（自动转换为 JSON）
- `{{temperature}}`: 温度参数
- `{{max_tokens}}`: 最大 token 数
- 以及其他自定义参数

### 扩展性

系统支持以下 AI 服务（开箱即用）：
- ✅ OpenAI (GPT-3.5, GPT-4, GPT-4o)
- ✅ Azure OpenAI
- ✅ Anthropic Claude
- ✅ DeepSeek
- ✅ 阿里云通义千问
- ✅ Google Gemini
- ✅ 任何兼容 OpenAI API 格式的服务

添加新的 AI 服务只需在 `config.json` 中添加对应的 Agent 配置。

------------------------------------------------------------------------

## 🔄 工作流程

1. **任务配置加载**
    - 从 `tasks.json` 读取启用的任务（或根据传参执行单任务）。
    - 每个任务包含关键词、页数、价格区间等筛选条件。
2. **爬虫执行**
    - 使用 Playwright
      打开搜索页，模拟用户筛选条件（最新、个人闲置、价格区间）。
    - 解析搜索结果，获取商品 ID 与链接。
    - 请求详情页，采集商品信息与卖家信息。
    - 自动检测反爬虫机制，如遇拦截会进入长时间休眠并退出。
3. **结果存储**
    - 每个任务的结果以 `jsonl` 格式保存，避免重复写入。
    - 提供基于关键词的结果查询与删除接口。
4. **Web 管理界面**
    - 登录认证基于 JWT。
    - 提供任务的增删改查、手动启动/停止、查看执行状态。
    - 结果支持分页查询与筛选。

------------------------------------------------------------------------

## 🧩 商品AI评估流程（ProductEvaluator）

对商品进行分步骤评估，减少大量token消耗。

---

### 一、流程概述

完整流程由以下三大步骤组成：

1. **标题筛选**  
   检查商品标题是否符合目标商品描述，确保分析范围正确。
    - 输入：目标商品描述 + 当前商品标题
    - 输出字段：
        - `analysis`: 标题匹配分析说明
        - `suggestion`: 建议度分数 (0–100)
        - `reason`: 简短中文理由

2. **卖家信息评估**  
   基于卖家信息（如信誉、销量、回复率等）计算卖家可信度。
    - 输入：卖家信息（除去卖家ID）
    - 输出字段：
        - `analysis`: 卖家信誉分析
        - `suggestion`: 卖家建议度分数
        - `reason`: 简短中文理由

3. **商品信息评估**  
   综合卖家可信度、目标商品描述与商品详情，对商品整体质量与匹配度进行分析。
    - 输入：目标商品描述 + 商品详情 + 上一步卖家分析结果
    - 输出字段：
        - `analysis`: 商品符合度分析
        - `suggestion`: 商品建议度分数
        - `reason`: 简短中文理由

---

### 二、评分与推荐逻辑

根据最后得分计算推荐结论：

| 建议度分数区间 | 结论文本   |
|---------|--------|
| 80–100  | 非常建议购买 |
| 60–79   | 建议购买   |
| 30–59   | 谨慎购买   |
| 0–29    | 不建议购买  |

最终输出示例：

```json
{
  "推荐度": 75,
  "建议": "建议购买",
  "原因": "商家信誉较好，商品描述基本符合目标商品。"
}
```

## 💖 鸣谢

本项目在开发过程中参考了以下项目：

- [ai-goofish-monitor](https://github.com/dingyufei615/ai-goofish-monitor)

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
