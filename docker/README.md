# Docker 构建说明

## 概述

为了优化构建效率和解决依赖编译问题，我们采用了分离式构建架构：

1. **Builder 镜像** (`dockerfile.dev`)：包含编译工具和预构建的 Python 依赖
2. **应用镜像** (主 `Dockerfile`)：基于 Builder 镜像，创建轻量级运行时镜像

## 架构优势

- **解决编译问题**：pyaudio 等需要 C 扩展的包在 builder 阶段预编译
- **减少镜像大小**：最终应用镜像不包含编译工具，更轻量
- **提高构建效率**：依赖变更时才重建 builder，代码变更直接使用预构建依赖
- **支持多架构**：自动构建 amd64 和 arm64 镜像

## GitHub Actions 自动化

### 🔧 Builder 镜像构建 (docker-build-builder.yml)

**触发条件：** 只有当以下文件发生变化时才会构建 builder 镜像

- `docker/dockerfile.dev`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/docker-build-builder.yml`

**构建目标：** 使用 `--target builder` 只构建第一阶段（编译阶段）

**镜像命名：** `ghcr.io/{repository}-builder:latest`

**包含内容：**

- 编译工具 (gcc, g++, libc6-dev)
- 音频处理开发库 (portaudio19-dev, libasound2-dev)
- 预构建的 Python 虚拟环境 (`/opt/venv`)

### 🚀 应用镜像构建 (docker-build-app.yml)

**触发条件：** 应用代码变更时触发

- `Dockerfile`
- `main.py`
- `bailing/**`
- `config/**`
- `plugins/**`
- `server/**`
- `.github/workflows/docker-build-app.yml`

**构建过程：**

1. 使用 builder 镜像作为依赖源
2. 创建轻量级运行时基础镜像
3. 从 builder 复制预构建的虚拟环境
4. 添加应用代码和运行时配置

**镜像特点：**

- 基于 bookworm-slim，体积更小
- 只包含运行时库，不含编译工具
- 自动创建非 root 用户运行

## 本地构建步骤

### 1. 构建 Builder 镜像

```bash
# 构建 builder 镜像（只构建 builder 阶段）
docker build -f docker/dockerfile.dev --target builder -t bailing-builder:latest .

# 推送到注册表
docker build -f docker/dockerfile.dev --target builder -t ghcr.io/your-username/bailing-builder:latest .
docker push ghcr.io/your-username/bailing-builder:latest
```

**注意：** 必须使用 `--target builder` 参数，因为我们只需要第一阶段的内容

### 2. 构建应用镜像

```bash
# 使用本地 builder 镜像
docker build --build-arg BUILDER_IMAGE=bailing-builder:latest -t bailing:latest .

# 使用注册表中的 builder 镜像（默认）
docker build -t bailing:latest .

# 指定特定的 builder 镜像
docker build --build-arg BUILDER_IMAGE=ghcr.io/your-username/bailing-builder:latest -t bailing:latest .
```

**说明：** 应用镜像会自动使用多阶段构建，从 builder 镜像复制预构建的依赖

## 工作流程优势

1. **解决编译问题**：pyaudio 等 C 扩展包在有编译工具的 builder 阶段预编译
2. **智能触发**：只有依赖变化时才重新构建 builder 镜像
3. **减少构建时间**：应用代码变更时，直接使用预构建依赖
4. **镜像体积优化**：最终应用镜像不包含编译工具，更轻量
5. **多架构支持**：自动构建 linux/amd64 和 linux/arm64
6. **自动化管理**：GitHub Actions 自动处理镜像构建和推送
7. **缓存优化**：每个阶段都有独立的缓存作用域

## 文件说明

- `docker/dockerfile.dev`：Builder 镜像的 Dockerfile，只包含编译阶段
- `Dockerfile`：应用镜像的 Dockerfile，基于 builder 镜像创建运行时镜像
- `.github/workflows/docker-build-builder.yml`：Builder 镜像构建工作流
- `.github/workflows/docker-build-app.yml`：应用镜像构建工作流

## 关键技术点

### Builder 阶段设计

- 使用 `python3.11-bookworm` 作为基础镜像，包含完整编译环境
- 安装 `portaudio19-dev`、`libasound2-dev` 等音频处理开发库
- 创建虚拟环境在 `/opt/venv`，预编译所有 Python 依赖
- 特别解决了 `pyaudio==0.2.14` 的编译问题

### 应用阶段设计

- 使用 `python3.11-bookworm-slim` 轻量级基础镜像
- 只安装运行时必需的库（如 `libportaudio2`、`libasound2`）
- 从 builder 阶段复制预构建的虚拟环境
- 创建非 root 用户 `appuser` 提高安全性

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

- Builder 镜像使用 `--target builder` 只构建第一阶段
- 应用镜像构建时会自动拉取最新的 builder 镜像
- 如果 builder 镜像不存在，应用镜像构建会失败，需要先构建 builder 镜像
- 建议在修改 `pyproject.toml` 或 `uv.lock` 后，先等待 builder 镜像构建完成再推送其他代码变更
- 本地测试时，确保使用正确的 `--target builder` 参数构建 builder 镜像

## 故障排除

### pyaudio 编译失败

如果遇到类似 `error: command 'gcc' failed` 的错误：

1. 检查 builder 镜像是否正确构建（使用 `--target builder`）
2. 确认 builder 镜像包含必要的编译工具和开发库
3. 验证应用镜像是否正确从 builder 复制虚拟环境

### 镜像拉取失败

如果应用构建时无法拉取 builder 镜像：

1. 检查 builder 镜像是否已推送到注册表
2. 确认镜像名称和标签是否正确
3. 验证访问权限是否足够
