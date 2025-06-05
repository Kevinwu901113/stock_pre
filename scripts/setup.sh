#!/bin/bash

# A股量化选股推荐系统环境设置脚本

set -e  # 遇到错误立即退出

echo "======================================"
echo "A股量化选股推荐系统环境设置"
echo "======================================"

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

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python版本: $PYTHON_VERSION"
    else
        log_error "Python3未安装，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查Node.js版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js版本: $NODE_VERSION"
    else
        log_error "Node.js未安装，请先安装Node.js 16+"
        exit 1
    fi
    
    # 检查npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        log_success "npm版本: $NPM_VERSION"
    else
        log_error "npm未安装"
        exit 1
    fi
    
    # 检查Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        log_success "Git版本: $GIT_VERSION"
    else
        log_warning "Git未安装，建议安装用于版本控制"
    fi
}

# 创建Python虚拟环境
setup_python_env() {
    log_info "设置Python虚拟环境..."
    
    # 检查是否已存在虚拟环境
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        log_success "Python虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "虚拟环境已激活"
    
    # 升级pip
    pip install --upgrade pip
    log_success "pip已升级到最新版本"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python依赖安装完成"
    else
        log_error "requirements.txt文件不存在"
        exit 1
    fi
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        if [ -f "package.json" ]; then
            npm install
            log_success "前端依赖安装完成"
        else
            log_error "frontend/package.json文件不存在"
            exit 1
        fi
        
        cd ..
    else
        log_error "frontend目录不存在"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "data/cache"
        "data/csv"
        "logs"
        "ai/models"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "创建目录: $dir"
        else
            log_info "目录已存在: $dir"
        fi
    done
}

# 复制配置文件
setup_config_files() {
    log_info "设置配置文件..."
    
    # 复制环境变量文件
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "已创建.env文件，请编辑填入实际配置"
    else
        log_info ".env文件已存在"
    fi
    
    # 复制API密钥文件
    if [ -f "config/api_keys.py.example" ] && [ ! -f "config/api_keys.py" ]; then
        cp config/api_keys.py.example config/api_keys.py
        log_success "已创建api_keys.py文件，请编辑填入实际API密钥"
    else
        log_info "api_keys.py文件已存在"
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 检查是否使用SQLite
    if grep -q "sqlite" config/settings.py; then
        log_info "使用SQLite数据库，无需额外初始化"
        return
    fi
    
    # 检查PostgreSQL连接
    if command -v psql &> /dev/null; then
        log_info "检测到PostgreSQL，可以手动运行初始化脚本:"
        log_info "psql -U postgres -f scripts/init.sql"
    else
        log_warning "未检测到PostgreSQL客户端"
        log_info "如果使用PostgreSQL，请确保数据库服务正在运行"
    fi
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 检查Python模块
    python3 -c "import fastapi, pandas, sqlalchemy" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "Python依赖验证通过"
    else
        log_error "Python依赖验证失败"
        return 1
    fi
    
    # 检查前端依赖
    if [ -d "frontend/node_modules" ]; then
        log_success "前端依赖验证通过"
    else
        log_error "前端依赖验证失败"
        return 1
    fi
    
    return 0
}

# 显示下一步操作
show_next_steps() {
    echo ""
    echo "======================================"
    echo "环境设置完成！"
    echo "======================================"
    echo ""
    echo "下一步操作:"
    echo "1. 编辑配置文件:"
    echo "   - .env (环境变量)"
    echo "   - config/api_keys.py (API密钥)"
    echo ""
    echo "2. 启动服务:"
    echo "   ./start.sh"
    echo ""
    echo "3. 访问应用:"
    echo "   - 前端: http://localhost:3000"
    echo "   - 后端API: http://localhost:8000"
    echo "   - API文档: http://localhost:8000/docs"
    echo ""
    echo "4. 可选操作:"
    echo "   - 下载AI模型: python scripts/download_models.py list"
    echo "   - 同步数据: python scripts/data_sync.py full"
    echo ""
}

# 主函数
main() {
    # 检查是否在项目根目录
    if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行设置步骤
    check_requirements
    setup_python_env
    install_python_deps
    install_frontend_deps
    create_directories
    setup_config_files
    init_database
    
    # 验证安装
    if verify_installation; then
        show_next_steps
    else
        log_error "安装验证失败，请检查错误信息"
        exit 1
    fi
}

# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --help, -h     显示帮助信息"
            echo "  --skip-deps    跳过依赖安装"
            echo "  --python-only  仅设置Python环境"
            echo "  --frontend-only 仅设置前端环境"
            exit 0
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 根据参数执行相应操作
if [ "$PYTHON_ONLY" = true ]; then
    check_requirements
    setup_python_env
    if [ "$SKIP_DEPS" != true ]; then
        install_python_deps
    fi
    create_directories
    setup_config_files
elif [ "$FRONTEND_ONLY" = true ]; then
    check_requirements
    if [ "$SKIP_DEPS" != true ]; then
        install_frontend_deps
    fi
else
    main
fi

log_success "设置脚本执行完成！"