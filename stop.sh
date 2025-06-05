#!/bin/bash

# A股量化选股推荐系统停止脚本

echo "=== 停止A股量化选股推荐系统 ==="

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm backend.pid
    else
        echo "后端服务未运行"
        rm -f backend.pid
    fi
else
    echo "未找到后端服务PID文件"
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm frontend.pid
    else
        echo "前端服务未运行"
        rm -f frontend.pid
    fi
else
    echo "未找到前端服务PID文件"
fi

# 强制停止可能残留的进程
echo "检查并停止残留进程..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo "所有服务已停止"