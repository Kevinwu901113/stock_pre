# A股量化选股推荐系统 - 多阶段构建Dockerfile
# 使用多阶段构建来优化镜像大小

# ================================
# 阶段1: 前端构建
# ================================
FROM node:18-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci --only=production

# 复制前端源码
COPY frontend/ ./

# 构建前端应用
RUN npm run build

# ================================
# 阶段2: 后端运行环境
# ================================
FROM python:3.11-slim AS backend

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 复制后端依赖文件
COPY backend/requirements.txt ./backend/

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# 复制后端源码
COPY backend/ ./backend/

# 从前端构建阶段复制构建结果
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# 创建必要目录
RUN mkdir -p backend/logs backend/data && \
    chown -R appuser:appuser /app

# 切换到应用用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "backend/main.py"]

# ================================
# 开发环境镜像（可选）
# ================================
FROM python:3.11-slim AS development

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（包含开发工具）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js（用于前端开发）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# 安装前端依赖
RUN cd frontend && npm install

# 创建必要目录
RUN mkdir -p backend/logs backend/data

# 暴露端口
EXPOSE 8000 3000

# 开发环境启动脚本
CMD ["bash", "-c", "cd backend && python main.py & cd frontend && npm run dev & wait"]