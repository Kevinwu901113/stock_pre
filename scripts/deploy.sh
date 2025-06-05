#!/bin/bash

# 股票推荐系统部署脚本
# 作者: AI Assistant
# 版本: 1.0
# 描述: 自动化部署股票推荐系统到生产环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="stock-recommendation"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

# 函数定义
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装，请先安装 Docker Compose"
    fi
    
    # 检查 Docker 服务状态
    if ! docker info &> /dev/null; then
        error "Docker 服务未运行，请启动 Docker 服务"
    fi
    
    log "✅ 系统依赖检查通过"
}

# 检查配置文件
check_config() {
    log "检查配置文件..."
    
    # 检查 Docker Compose 文件
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        error "Docker Compose 文件不存在: $DOCKER_COMPOSE_FILE"
    fi
    
    # 检查环境变量文件
    if [[ ! -f "$ENV_FILE" ]]; then
        warn "环境变量文件不存在: $ENV_FILE，将创建默认配置"
        create_env_file
    fi
    
    # 验证 Docker Compose 文件语法
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" config &> /dev/null; then
        error "Docker Compose 文件语法错误"
    fi
    
    log "✅ 配置文件检查通过"
}

# 创建默认环境变量文件
create_env_file() {
    log "创建默认环境变量文件: $ENV_FILE"
    
    cat > "$ENV_FILE" << EOF
# 生产环境配置
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=postgresql://stock_user:stock_password@postgres:5432/stock_recommendation
POSTGRES_DB=stock_recommendation
POSTGRES_USER=stock_user
POSTGRES_PASSWORD=stock_password

# Redis 配置
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=redis_password

# JWT 配置
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com

# API 配置
API_RATE_LIMIT=100
CACHE_TTL=300

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 数据源配置
TUSHARE_TOKEN=your_tushare_token
SINA_API_KEY=your_sina_api_key

# 监控配置
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=admin123
EOF
    
    warn "请编辑 $ENV_FILE 文件，设置正确的配置值"
}

# 创建必要目录
create_directories() {
    log "创建必要目录..."
    
    directories=(
        "./data/postgres"
        "./data/redis"
        "./data/csv"
        "./logs"
        "./logs/nginx"
        "$BACKUP_DIR"
        "./ssl"
        "./config/nginx/conf.d"
        "./config/grafana/provisioning"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "创建目录: $dir"
        fi
    done
    
    # 设置权限
    chmod 755 ./data/postgres
    chmod 755 ./data/redis
    chmod 755 ./logs
    
    log "✅ 目录创建完成"
}

# 备份数据
backup_data() {
    if [[ "$1" == "--skip-backup" ]]; then
        log "跳过数据备份"
        return
    fi
    
    log "备份现有数据..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
    
    # 检查是否有运行中的容器
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        log "发现运行中的服务，创建数据备份..."
        
        # 备份数据库
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_dump -U stock_user stock_recommendation > "$BACKUP_DIR/db_backup_$timestamp.sql"; then
            log "数据库备份完成: $BACKUP_DIR/db_backup_$timestamp.sql"
        else
            warn "数据库备份失败"
        fi
        
        # 备份数据目录
        if tar -czf "$backup_file" ./data ./logs 2>/dev/null; then
            log "数据目录备份完成: $backup_file"
        else
            warn "数据目录备份失败"
        fi
    else
        log "没有运行中的服务，跳过备份"
    fi
}

# 拉取最新镜像
pull_images() {
    log "拉取最新 Docker 镜像..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" pull; then
        log "✅ 镜像拉取完成"
    else
        error "镜像拉取失败"
    fi
}

# 构建自定义镜像
build_images() {
    log "构建自定义镜像..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache; then
        log "✅ 镜像构建完成"
    else
        error "镜像构建失败"
    fi
}

# 停止现有服务
stop_services() {
    log "停止现有服务..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" down; then
        log "✅ 服务停止完成"
    else
        warn "服务停止时出现警告"
    fi
}

# 启动服务
start_services() {
    log "启动服务..."
    
    # 使用环境变量文件启动
    if docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d; then
        log "✅ 服务启动完成"
    else
        error "服务启动失败"
    fi
}

# 等待服务就绪
wait_for_services() {
    log "等待服务就绪..."
    
    max_attempts=30
    attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "healthy\|Up"; then
            log "✅ 服务已就绪"
            return 0
        fi
        
        attempt=$((attempt + 1))
        info "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
    done
    
    error "服务启动超时"
}

# 运行健康检查
health_check() {
    log "运行健康检查..."
    
    # 检查后端 API
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "✅ 后端 API 健康检查通过"
    else
        error "后端 API 健康检查失败"
    fi
    
    # 检查前端
    if curl -f http://localhost:3000 &> /dev/null; then
        log "✅ 前端健康检查通过"
    else
        error "前端健康检查失败"
    fi
    
    # 检查数据库连接
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U stock_user &> /dev/null; then
        log "✅ 数据库连接检查通过"
    else
        error "数据库连接检查失败"
    fi
    
    # 检查 Redis 连接
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli -a redis_password ping &> /dev/null; then
        log "✅ Redis 连接检查通过"
    else
        error "Redis 连接检查失败"
    fi
}

# 初始化数据
init_data() {
    if [[ "$1" == "--skip-init" ]]; then
        log "跳过数据初始化"
        return
    fi
    
    log "初始化数据..."
    
    # 运行数据库迁移
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python -m alembic upgrade head; then
        log "✅ 数据库迁移完成"
    else
        warn "数据库迁移失败或已是最新版本"
    fi
    
    # 生成测试数据（如果需要）
    if [[ -f "scripts/prepare_test_data.py" ]]; then
        log "生成测试数据..."
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python scripts/prepare_test_data.py --days 30; then
            log "✅ 测试数据生成完成"
        else
            warn "测试数据生成失败"
        fi
    fi
}

# 显示部署信息
show_deployment_info() {
    log "部署完成！"
    
    echo -e "\n${GREEN}=== 部署信息 ===${NC}"
    echo -e "${BLUE}项目名称:${NC} $PROJECT_NAME"
    echo -e "${BLUE}部署时间:${NC} $(date)"
    echo -e "${BLUE}Docker Compose 文件:${NC} $DOCKER_COMPOSE_FILE"
    echo -e "${BLUE}环境变量文件:${NC} $ENV_FILE"
    
    echo -e "\n${GREEN}=== 服务访问地址 ===${NC}"
    echo -e "${BLUE}前端应用:${NC} http://localhost:3000"
    echo -e "${BLUE}后端 API:${NC} http://localhost:8000"
    echo -e "${BLUE}API 文档:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}Nginx (开发):${NC} http://localhost:8080"
    echo -e "${BLUE}Prometheus:${NC} http://localhost:9090"
    echo -e "${BLUE}Grafana:${NC} http://localhost:3001 (admin/admin123)"
    
    echo -e "\n${GREEN}=== 常用命令 ===${NC}"
    echo -e "${BLUE}查看服务状态:${NC} docker-compose -f $DOCKER_COMPOSE_FILE ps"
    echo -e "${BLUE}查看服务日志:${NC} docker-compose -f $DOCKER_COMPOSE_FILE logs -f [service_name]"
    echo -e "${BLUE}停止所有服务:${NC} docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo -e "${BLUE}重启服务:${NC} docker-compose -f $DOCKER_COMPOSE_FILE restart [service_name]"
    
    echo -e "\n${GREEN}=== 监控和日志 ===${NC}"
    echo -e "${BLUE}应用日志目录:${NC} ./logs/"
    echo -e "${BLUE}Nginx 日志:${NC} ./logs/nginx/"
    echo -e "${BLUE}备份目录:${NC} $BACKUP_DIR"
    
    echo -e "\n${YELLOW}注意事项:${NC}"
    echo -e "1. 请确保防火墙已开放相应端口"
    echo -e "2. 生产环境请修改默认密码"
    echo -e "3. 定期备份数据库和重要数据"
    echo -e "4. 监控系统资源使用情况"
}

# 清理函数
cleanup() {
    log "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 信号处理
trap cleanup EXIT

# 显示帮助信息
show_help() {
    echo "股票推荐系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --skip-backup       跳过数据备份"
    echo "  --skip-init         跳过数据初始化"
    echo "  --build-only        仅构建镜像，不启动服务"
    echo "  --start-only        仅启动服务，不构建镜像"
    echo "  --dev               使用开发环境配置"
    echo ""
    echo "示例:"
    echo "  $0                  完整部署"
    echo "  $0 --skip-backup    部署但跳过备份"
    echo "  $0 --build-only     仅构建镜像"
    echo "  $0 --dev            开发环境部署"
}

# 主函数
main() {
    # 解析命令行参数
    SKIP_BACKUP=false
    SKIP_INIT=false
    BUILD_ONLY=false
    START_ONLY=false
    DEV_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-init)
                SKIP_INIT=true
                shift
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --start-only)
                START_ONLY=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                DOCKER_COMPOSE_FILE="docker-compose.yml"
                ENV_FILE=".env"
                shift
                ;;
            *)
                error "未知选项: $1"
                ;;
        esac
    done
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "开始部署 $PROJECT_NAME..."
    
    # 执行部署步骤
    check_dependencies
    check_config
    create_directories
    
    if [[ "$BUILD_ONLY" == "true" ]]; then
        build_images
        log "✅ 镜像构建完成"
        exit 0
    fi
    
    if [[ "$START_ONLY" == "false" ]]; then
        if [[ "$SKIP_BACKUP" == "false" ]]; then
            backup_data
        fi
        
        pull_images
        build_images
        stop_services
    fi
    
    start_services
    wait_for_services
    health_check
    
    if [[ "$SKIP_INIT" == "false" ]]; then
        init_data
    fi
    
    show_deployment_info
    
    log "🎉 部署成功完成！"
}

# 运行主函数
main "$@"