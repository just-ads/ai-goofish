# ---------- 构建阶段 ----------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 安装系统依赖 (编译和 playwright 所需)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget unzip git build-essential \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install --with-deps chromium

# ---------- 运行阶段 ----------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 安装运行时必须的库（少量）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段拷贝 Python 包和浏览器
COPY --from=builder /install /usr/local
COPY --from=builder /ms-playwright /ms-playwright

# 拷贝源码
COPY . .

# 非 root 用户
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["python", "start.py"]
