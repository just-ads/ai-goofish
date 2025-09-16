# ---------- 构建阶段 ----------
FROM python:3.12-slim AS builder

# 设置元数据
LABEL maintainer="your-email@example.com"
LABEL description="Application with Python 3.12 and Playwright"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 安装系统依赖 (编译和 playwright 所需)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget unzip git build-essential \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建虚拟环境
RUN python -m venv /opt/venv

COPY requirements.txt .

# 在虚拟环境中安装Python依赖和Playwright
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install --with-deps chromium

# ---------- 运行阶段 ----------
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 安装运行时必须的库（最小化）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# 从builder阶段拷贝虚拟环境和浏览器
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /ms-playwright /ms-playwright

# 创建应用目录并设置权限
RUN mkdir -p /app && chown nobody:nogroup /app

# 切换到安全的非特权用户
USER nobody

# 拷贝源码（使用正确的权限）
COPY --chown=nobody:nogroup . .

# 健康检查（可选）
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 使用exec形式启动应用
CMD ["python", "start.py"]