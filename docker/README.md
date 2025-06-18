# Docker 构建说明

## 概述

为了优化 GitHub 空间的磁盘使用，我们将多阶段构建拆分为两个步骤：

1. **预构建 Builder 镜像**：包含所有系统依赖和 Python 依赖
2. **应用镜像**：基于 Builder 镜像，只包含应用代码

## GitHub Actions 自动化

### 🔧 Builder 镜像构建 (docker-build-builder.yml)

**触发条件：** 只有当以下文件发生变化时才会构建 builder 镜像

- `docker/dockerfile.dev`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/docker-build-builder.yml`

**镜像命名：** `ghcr.io/{repository}-builder:latest`

### 🚀 应用镜像构建 (docker-build-app.yml)

**触发条件：** 除了 builder 相关文件外的其他代码变更

**依赖：** 自动拉取最新的 builder 镜像作为基础

## 本地构建步骤

### 1. 构建 Builder 镜像

```bash
# 构建 builder 镜像
docker build -f docker/dockerfile.dev -t bailing-builder:latest .

# 或者推送到注册表
docker build -f docker/dockerfile.dev -t ghcr.io/your-username/bailing-builder:latest .
docker push ghcr.io/your-username/bailing-builder:latest
```

### 2. 构建应用镜像

```bash
# 使用本地 builder 镜像
docker build -t bailing:latest .

# 使用注册表中的 builder 镜像
docker build --build-arg BUILDER_IMAGE=ghcr.io/your-username/bailing-builder:latest -t bailing:latest .
```

## 工作流程优势

1. **智能触发**：只有依赖变化时才重新构建 builder 镜像
2. **减少构建时间**：应用代码变更时，直接基于已有的 builder 镜像构建
3. **自动化管理**：GitHub Actions 自动处理镜像构建和推送
4. **缓存优化**：每个阶段都有独立的缓存作用域

## 文件说明

- `docker/dockerfile.dev`：Builder 镜像的 Dockerfile
- `Dockerfile`：应用镜像的 Dockerfile，支持通过 build-arg 指定 builder 镜像
- `.github/workflows/docker-build-builder.yml`：Builder 镜像构建工作流
- `.github/workflows/docker-build-app.yml`：应用镜像构建工作流

## 镜像标签策略

### Builder 镜像标签

- `latest`：主分支的最新版本
- `builder-{version}`：语义化版本标签
- `{branch}-builder`：分支构建标签

### 应用镜像标签

- `latest`：主分支的最新版本
- `{version}`：语义化版本标签
- `{branch}`：分支构建标签

## 注意事项

- Builder 镜像会自动推送到 GitHub Container Registry
- 应用镜像构建时会自动拉取最新的 builder 镜像
- 如果 builder 镜像不存在，应用镜像构建会失败，需要先构建 builder 镜像
- 建议在修改依赖后，先等待 builder 镜像构建完成再推送其他代码变更
