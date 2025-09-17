# ---------- 构建阶段 ----------
FROM python:3.12-slim AS builder

WORKDIR /build

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# 创建虚拟环境
RUN python -m venv /opt/venv

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ---------- 运行阶段 ----------
FROM python:3.12-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    RUNNING_IN_DOCKER=true \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"


COPY --from=builder /opt/venv /opt/venv

# 安装Playwright
RUN playwright install --with-deps --only-shell chromium

COPY . .

EXPOSE 8000

# 使用exec形式启动应用
CMD ["python", "start.py"]