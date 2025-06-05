#!/bin/bash

# A股量化选股推荐系统启动脚本

echo "=== A股量化选股推荐系统启动脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装npm"
    exit 1
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data/csv
mkdir -p data/cache
mkdir -p logs
mkdir -p ai/models

# 检查并安装Python依赖
echo "检查Python依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt文件"
    exit 1
fi

# 安装Python依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt

# 检查前端依赖
echo "检查前端依赖..."
cd frontend
if [ ! -f "package.json" ]; then
    echo "错误: 未找到package.json文件"
    exit 1
fi

# 安装前端依赖
echo "安装前端依赖..."
npm install

# 返回根目录
cd ..

# 启动服务
echo "启动服务..."

# 启动后端服务
echo "启动后端API服务..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "后端服务已启动，PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端服务
echo "启动前端开发服务器..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "前端服务已启动，PID: $FRONTEND_PID"

# 保存PID到文件
echo $BACKEND_PID > ../backend.pid
echo $FRONTEND_PID > ../frontend.pid

echo ""
echo "=== 服务启动完成 ==="
echo "前端地址: http://localhost:3000"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "或运行 ./stop.sh 停止服务"

# 等待用户中断
wait