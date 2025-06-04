#!/bin/bash

# A股量化选股推荐系统 - 一键启动脚本
# Author: Stock Recommendation System
# Description: 自动检查环境、安装依赖并启动前后端服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python版本
check_python() {
    log_info "检查Python环境..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            log_success "Python版本: $PYTHON_VERSION ✓"
            PYTHON_CMD="python3"
        else
            log_error "需要Python 3.8+，当前版本: $PYTHON_VERSION"
            exit 1
        fi
    elif command_exists python; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            log_success "Python版本: $PYTHON_VERSION ✓"
            PYTHON_CMD="python"
        else
            log_error "需要Python 3.8+，当前版本: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
}

# 检查Node.js版本
check_nodejs() {
    log_info "检查Node.js环境..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
        
        if [ "$NODE_MAJOR" -ge 16 ]; then
            log_success "Node.js版本: v$NODE_VERSION ✓"
        else
            log_error "需要Node.js 16+，当前版本: v$NODE_VERSION"
            exit 1
        fi
    else
        log_error "未找到Node.js，请先安装Node.js 16+"
        exit 1
    fi
    
    if ! command_exists npm; then
        log_error "未找到npm，请确保npm已正确安装"
        exit 1
    fi
}

# 检查Redis（可选）
check_redis() {
    log_info "检查Redis服务..."
    
    if command_exists redis-server; then
        if pgrep redis-server > /dev/null; then
            log_success "Redis服务正在运行 ✓"
        else
            log_warning "Redis已安装但未运行，尝试启动..."
            if command_exists systemctl; then
                sudo systemctl start redis-server 2>/dev/null || true
            else
                redis-server --daemonize yes 2>/dev/null || true
            fi
            
            sleep 2
            if pgrep redis-server > /dev/null; then
                log_success "Redis服务启动成功 ✓"
            else
                log_warning "Redis启动失败，将使用内存缓存"
            fi
        fi
    else
        log_warning "Redis未安装，将使用内存缓存"
    fi
}

# 设置后端环境
setup_backend() {
    log_info "设置后端环境..."
    
    cd backend
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    # 创建必要目录
    mkdir -p logs data
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，创建默认配置..."
        cat > .env << EOF
# 基础配置
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据源配置
TUSHARE_TOKEN=your_tushare_token_here
AKSHARE_ENABLED=true

# 缓存配置
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
CACHE_EXPIRE_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# AI配置（可选）
AI_DEFAULT_PROVIDER=mock
AI_ENABLED_PROVIDERS=["mock"]
EOF
        log_warning "请编辑 backend/.env 文件，设置您的API密钥"
    fi
    
    cd ..
    log_success "后端环境设置完成 ✓"
}

# 设置前端环境
setup_frontend() {
    log_info "设置前端环境..."
    
    cd frontend
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install
    
    cd ..
    log_success "前端环境设置完成 ✓"
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    cd backend
    source venv/bin/activate
    
    # 后台启动后端
    nohup $PYTHON_CMD main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否启动成功
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_success "后端服务启动成功 (PID: $BACKEND_PID) ✓"
        log_info "后端服务地址: http://localhost:8000"
        log_info "API文档地址: http://localhost:8000/docs"
    else
        log_error "后端服务启动失败，请检查日志: logs/backend.log"
        exit 1
    fi
    
    cd ..
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    cd frontend
    
    # 后台启动前端
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    # 等待服务启动
    sleep 5
    
    # 检查服务是否启动成功
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_success "前端服务启动成功 (PID: $FRONTEND_PID) ✓"
        log_info "前端服务地址: http://localhost:3000"
    else
        log_error "前端服务启动失败，请检查日志: logs/frontend.log"
        exit 1
    fi
    
    cd ..
}

# 显示服务状态
show_status() {
    echo
    log_success "=== 服务启动完成 ==="
    echo
    echo "📊 前端应用: http://localhost:3000"
    echo "🔧 后端API: http://localhost:8000"
    echo "📖 API文档: http://localhost:8000/docs"
    echo
    echo "📝 日志文件:"
    echo "   - 后端日志: logs/backend.log"
    echo "   - 前端日志: logs/frontend.log"
    echo "   - 应用日志: backend/logs/app.log"
    echo
    echo "🛑 停止服务: ./stop.sh"
    echo "📊 查看状态: ./status.sh"
    echo
}

# 创建停止脚本
create_stop_script() {
    cat > stop.sh << 'EOF'
#!/bin/bash

# 停止服务脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid
            fi
            log_success "${service_name}服务已停止"
        else
            log_info "${service_name}服务未运行"
        fi
        rm -f "$pid_file"
    else
        log_info "${service_name}服务PID文件不存在"
    fi
}

log_info "正在停止服务..."

# 停止后端服务
stop_service "后端" "logs/backend.pid"

# 停止前端服务
stop_service "前端" "logs/frontend.pid"

log_success "所有服务已停止"
EOF
    
    chmod +x stop.sh
}

# 创建状态检查脚本
create_status_script() {
    cat > status.sh << 'EOF'
#!/bin/bash

# 服务状态检查脚本

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
                echo -e "${GREEN}✓${NC} ${service_name}服务运行中 (PID: $pid, Port: $port)"
            else
                echo -e "${YELLOW}⚠${NC} ${service_name}进程存在但端口未监听 (PID: $pid)"
            fi
        else
            echo -e "${RED}✗${NC} ${service_name}服务已停止"
        fi
    else
        echo -e "${RED}✗${NC} ${service_name}服务未启动"
    fi
}

echo "=== 服务状态检查 ==="
echo

check_service "后端" "logs/backend.pid" "8000"
check_service "前端" "logs/frontend.pid" "3000"

echo
echo "=== 服务地址 ==="
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8000"
echo "文档: http://localhost:8000/docs"
EOF
    
    chmod +x status.sh
}

# 主函数
main() {
    echo "=================================="
    echo "  A股量化选股推荐系统 - 一键启动"
    echo "=================================="
    echo
    
    # 创建日志目录
    mkdir -p logs
    
    # 环境检查
    check_python
    check_nodejs
    check_redis
    
    echo
    log_info "开始设置项目环境..."
    
    # 环境设置
    setup_backend
    setup_frontend
    
    echo
    log_info "开始启动服务..."
    
    # 启动服务
    start_backend
    start_frontend
    
    # 创建管理脚本
    create_stop_script
    create_status_script
    
    # 显示状态
    show_status
}

# 信号处理
trap 'log_error "启动过程被中断"; exit 1' INT TERM

# 检查是否在项目根目录
if [ ! -f "project_plan.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "请在项目根目录下运行此脚本"
    exit 1
fi

# 运行主函数
main "$@"