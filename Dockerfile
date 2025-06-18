# 使用预构建的builder镜像作为基础
# 可以通过build-arg指定builder镜像
ARG BUILDER_IMAGE=ghcr.io/yeisme/bailing-builder:latest
FROM ${BUILDER_IMAGE} AS base

# 设置工作目录
WORKDIR /app

# 拷贝最新的源代码（覆盖builder中的代码）
COPY . .

# 如果依赖有变化，重新同步
RUN uv sync --frozen

# 设置环境变量
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "main.py", "--config_path", "config/config.yaml"] 
