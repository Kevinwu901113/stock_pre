# Makefile for Stock Recommendation System
# 股票推荐系统构建和管理脚本

.PHONY: help install dev test clean build run stop logs docker-build docker-run docker-stop

# 默认目标
help:
	@echo "Stock Recommendation System - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install     - Install all dependencies"
	@echo "  dev         - Setup development environment"
	@echo "  init        - Initialize project (first time setup)"
	@echo ""
	@echo "Development Commands:"
	@echo "  run         - Start all services (backend + frontend)"
	@echo "  run-backend - Start backend server only"
	@echo "  run-frontend- Start frontend development server only"
	@echo "  stop        - Stop all running services"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-api    - Run API tests only"
	@echo "  test-cov    - Run tests with coverage report"
	@echo ""
	@echo "Data Commands:"
	@echo "  sync-data   - Sync stock data"
	@echo "  download-models - Download AI models"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-run  - Run with Docker Compose"
	@echo "  docker-stop - Stop Docker containers"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean       - Clean temporary files"
	@echo "  logs        - Show application logs"
	@echo "  format      - Format code"
	@echo "  lint        - Run code linting"

# 安装依赖
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed successfully!"

# 开发环境设置
dev: install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	@if [ ! -f config/api_keys.py ]; then cp config/api_keys.py.example config/api_keys.py; echo "Created API keys config from template"; fi
	mkdir -p logs data/cache ai/models
	@echo "Development environment ready!"

# 项目初始化（首次设置）
init:
	@echo "Initializing project..."
	./scripts/setup.sh
	@echo "Project initialized successfully!"

# 运行所有服务
run:
	@echo "Starting all services..."
	docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	sleep 5
	@echo "Starting backend server..."
	nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
	@echo "Starting frontend development server..."
	cd frontend && nohup npm run dev > ../logs/frontend.log 2>&1 &
	@echo "All services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

# 仅运行后端
run-backend:
	@echo "Starting backend server..."
	docker-compose up -d postgres redis
	sleep 3
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 仅运行前端
run-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

# 停止所有服务
stop:
	@echo "Stopping all services..."
	@pkill -f "uvicorn backend.app.main:app" || true
	@pkill -f "npm run dev" || true
	docker-compose down
	@echo "All services stopped!"

# 运行测试
test:
	@echo "Running all tests..."
	pytest tests/ -v

# 运行单元测试
test-unit:
	@echo "Running unit tests..."
	pytest tests/ -v -m "unit"

# 运行API测试
test-api:
	@echo "Running API tests..."
	pytest tests/test_api.py -v

# 运行测试并生成覆盖率报告
test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# 同步股票数据
sync-data:
	@echo "Syncing stock data..."
	python scripts/data_sync.py

# 下载AI模型
download-models:
	@echo "Downloading AI models..."
	python scripts/download_models.py

# Docker构建
docker-build:
	@echo "Building Docker images..."
	docker-compose build

# Docker运行
docker-run:
	@echo "Starting services with Docker..."
	docker-compose up -d
	@echo "Services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

# Docker停止
docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

# 清理临时文件
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	rm -rf frontend/dist/ frontend/node_modules/.cache/
	rm -f logs/*.log
	@echo "Cleanup completed!"

# 查看日志
logs:
	@echo "Recent application logs:"
	@echo "=== Backend Logs ==="
	@tail -n 50 logs/backend.log 2>/dev/null || echo "No backend logs found"
	@echo ""
	@echo "=== Frontend Logs ==="
	@tail -n 50 logs/frontend.log 2>/dev/null || echo "No frontend logs found"

# 代码格式化
format:
	@echo "Formatting Python code..."
	black . --exclude="/(venv|env|\.venv|\.env|node_modules)/"
	isort . --skip venv --skip env --skip .venv --skip .env --skip node_modules
	@echo "Formatting frontend code..."
	cd frontend && npm run format 2>/dev/null || echo "Frontend formatting not configured"
	@echo "Code formatting completed!"

# 代码检查
lint:
	@echo "Running Python linting..."
	flake8 . --exclude=venv,env,.venv,.env,node_modules --max-line-length=88
	mypy . --ignore-missing-imports --exclude="(venv|env|\.venv|\.env|node_modules)/"
	@echo "Running frontend linting..."
	cd frontend && npm run lint 2>/dev/null || echo "Frontend linting not configured"
	@echo "Linting completed!"

# 数据库迁移
db-migrate:
	@echo "Running database migrations..."
	psql -h localhost -U postgres -d stock_db -f scripts/init.sql
	@echo "Database migration completed!"

# 备份数据库
db-backup:
	@echo "Creating database backup..."
	mkdir -p backups
	pg_dump -h localhost -U postgres stock_db > backups/stock_db_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created in backups/"

# 健康检查
health:
	@echo "Checking service health..."
	@echo "Backend API:"
	@curl -s http://localhost:8000/health || echo "Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend OK" || echo "Frontend not responding"
	@echo ""
	@echo "Database:"
	@docker-compose exec postgres pg_isready -U postgres && echo "Database OK" || echo "Database not responding"
	@echo ""
	@echo "Redis:"
	@docker-compose exec redis redis-cli ping && echo "Redis OK" || echo "Redis not responding"

# 性能测试
perf-test:
	@echo "Running performance tests..."
	@echo "This would run load testing tools like locust or ab"
	@echo "Performance testing not implemented yet"

# 安全扫描
security-scan:
	@echo "Running security scan..."
	bandit -r . -x venv,env,.venv,.env,node_modules,tests
	@echo "Security scan completed!"

# 生成API文档
docs:
	@echo "Generating API documentation..."
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "ReDoc documentation available at: http://localhost:8000/redoc"

# 版本信息
version:
	@echo "Stock Recommendation System"
	@echo "Version: 1.0.0"
	@echo "Python: $(shell python --version)"
	@echo "Node.js: $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"