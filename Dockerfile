# syntax=docker/dockerfile:1

# 第一阶段：构建基础镜像，安装系统依赖
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

# 设置工作目录
WORKDIR /app

# 安装系统依赖 - 分层缓存优化
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 音频处理依赖
    portaudio19-dev \
    libasound2-dev \
    # 编译依赖
    gcc \
    g++ \
    libc6-dev \
    # FFmpeg 用于音频处理
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    # 其他工具
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 第二阶段：Python 依赖安装
FROM base AS deps

# 拷贝依赖文件，利用 Docker 层缓存
COPY pyproject.toml uv.lock ./

# 使用 uv 安装依赖到虚拟环境
RUN uv sync --frozen --no-install-project

# 第三阶段：应用构建
FROM deps AS build

# 拷贝源代码
COPY . .

# 安装项目本身
RUN uv sync --frozen

# 第四阶段：运行时镜像
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

# 安装运行时系统依赖（不包含构建工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    libasound2-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 从构建阶段拷贝虚拟环境
COPY --from=build /app/.venv /app/.venv

# 拷贝应用代码
COPY --from=build /app .

# 创建必要的目录
RUN mkdir -p tmp config models documents

# 设置环境变量
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 暴露端口（根据你的应用需要调整）
EXPOSE 5000

# 设置非 root 用户
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup && \
    chown -R appuser:appgroup /app

USER appuser

# 启动应用
CMD ["python", "main.py", "--config_path", "config/config.yaml"] 
