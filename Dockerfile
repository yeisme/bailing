# 使用预构建的builder镜像作为基础
# 可以通过build-arg指定builder镜像
ARG BUILDER_IMAGE=ghcr.io/yeisme/bailing-builder:latest
FROM ${BUILDER_IMAGE} AS builder

# ---- 最终运行阶段 ----
# 使用轻量级基础镜像
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS final

# 设置工作目录
WORKDIR /app

# 安装运行时的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 运行时音频库
    libasound2 \
    libportaudio2 \
    # FFmpeg 运行时库
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从 builder 阶段拷贝已经安装好依赖的虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 拷贝最新的源代码
COPY . .

# 创建必要的目录
RUN mkdir -p tmp config models documents

# 设置非 root 用户
RUN addgroup --gid 1001 --system appgroup && \
    adduser --uid 1001 --system --ingroup appgroup --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appgroup /app

USER appuser

# 设置环境变量，指向拷贝过来的虚拟环境
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "main.py", "--config_path", "config/config.yaml"] 
