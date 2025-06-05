# 贡献指南 (Contributing Guide)

感谢您对股票推荐系统项目的关注！我们欢迎所有形式的贡献，包括但不限于代码、文档、测试、问题报告和功能建议。

## 目录

- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交流程](#提交流程)
- [问题报告](#问题报告)
- [功能请求](#功能请求)
- [代码审查](#代码审查)
- [测试要求](#测试要求)

## 开发环境设置

### 前置要求

- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL 13+
- Redis 6+

### 快速开始

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd stock
   ```

2. **设置开发环境**
   ```bash
   make init
   # 或者手动执行
   ./scripts/setup.sh
   ```

3. **安装依赖**
   ```bash
   make install
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   cp config/api_keys.py.example config/api_keys.py
   # 编辑配置文件，填入必要的API密钥
   ```

5. **启动服务**
   ```bash
   make run
   ```

## 代码规范

### Python 代码规范

我们遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 标准，并使用以下工具：

- **格式化**: Black
- **导入排序**: isort
- **代码检查**: flake8
- **类型检查**: mypy

运行代码格式化：
```bash
make format
```

运行代码检查：
```bash
make lint
```

### 前端代码规范

- 使用 Vue 3 Composition API
- 遵循 Vue 官方风格指南
- 使用 TypeScript
- 使用 ESLint 和 Prettier

### 命名约定

- **Python**:
  - 类名: `PascalCase`
  - 函数/变量: `snake_case`
  - 常量: `UPPER_SNAKE_CASE`
  - 私有成员: `_leading_underscore`

- **JavaScript/TypeScript**:
  - 类名: `PascalCase`
  - 函数/变量: `camelCase`
  - 常量: `UPPER_SNAKE_CASE`
  - 组件: `PascalCase`

### 文档规范

- 所有公共函数和类必须有文档字符串
- 使用 Google 风格的文档字符串
- API 接口必须有完整的注释
- 复杂算法需要详细注释

示例：
```python
def calculate_moving_average(prices: List[float], period: int) -> List[float]:
    """
    计算移动平均线。
    
    Args:
        prices: 价格列表
        period: 计算周期
        
    Returns:
        移动平均线数据列表
        
    Raises:
        ValueError: 当period小于1或大于prices长度时
    """
    pass
```

## 提交流程

### 分支策略

我们使用 Git Flow 分支模型：

- `main`: 主分支，包含稳定的生产代码
- `develop`: 开发分支，包含最新的开发代码
- `feature/*`: 功能分支，用于开发新功能
- `bugfix/*`: 修复分支，用于修复bug
- `hotfix/*`: 热修复分支，用于紧急修复

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型 (type):
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(strategies): add moving average cross strategy

Implement a new strategy based on moving average crossover signals.
Includes buy/sell signal generation and confidence calculation.

Closes #123
```

### Pull Request 流程

1. **创建功能分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **开发和测试**
   ```bash
   # 开发代码
   # 运行测试
   make test
   # 检查代码质量
   make lint
   ```

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

4. **创建 Pull Request**
   - 在 GitHub/GitLab 上创建 PR
   - 填写 PR 模板
   - 请求代码审查

5. **代码审查和合并**
   - 响应审查意见
   - 修复问题
   - 等待批准和合并

## 问题报告

在报告问题时，请提供以下信息：

### Bug 报告模板

```markdown
## Bug 描述
简要描述遇到的问题

## 复现步骤
1. 执行步骤1
2. 执行步骤2
3. 看到错误

## 期望行为
描述期望的正确行为

## 实际行为
描述实际发生的行为

## 环境信息
- 操作系统: [e.g. Ubuntu 20.04]
- Python 版本: [e.g. 3.9.7]
- Node.js 版本: [e.g. 16.14.0]
- 浏览器: [e.g. Chrome 96]

## 附加信息
- 错误日志
- 截图
- 其他相关信息
```

## 功能请求

### 功能请求模板

```markdown
## 功能描述
简要描述建议的功能

## 问题背景
描述当前存在的问题或需求

## 解决方案
描述建议的解决方案

## 替代方案
描述考虑过的其他解决方案

## 附加信息
提供任何其他相关信息
```

## 代码审查

### 审查清单

**功能性**
- [ ] 代码实现了预期功能
- [ ] 边界条件处理正确
- [ ] 错误处理完善
- [ ] 性能考虑合理

**代码质量**
- [ ] 代码清晰易读
- [ ] 命名规范一致
- [ ] 注释充分
- [ ] 无重复代码

**测试**
- [ ] 包含单元测试
- [ ] 测试覆盖率充分
- [ ] 集成测试通过
- [ ] 手动测试验证

**安全性**
- [ ] 无安全漏洞
- [ ] 输入验证完善
- [ ] 敏感信息保护
- [ ] 权限控制正确

### 审查指导原则

1. **建设性反馈**: 提供具体、可操作的建议
2. **及时响应**: 在24小时内完成审查
3. **尊重他人**: 保持专业和友善的态度
4. **学习机会**: 将审查视为学习和分享的机会

## 测试要求

### 测试类型

1. **单元测试**
   - 覆盖所有公共函数
   - 测试边界条件
   - 模拟外部依赖

2. **集成测试**
   - 测试模块间交互
   - 测试数据库操作
   - 测试API接口

3. **端到端测试**
   - 测试完整用户流程
   - 测试前后端集成
   - 测试部署环境

### 测试命令

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行API测试
make test-api

# 生成覆盖率报告
make test-cov
```

### 测试覆盖率要求

- 新代码: 90%+
- 核心模块: 95%+
- 整体项目: 80%+

## 发布流程

### 版本号规范

使用 [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的API变更
- `MINOR`: 向后兼容的功能新增
- `PATCH`: 向后兼容的问题修正

### 发布步骤

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建发布分支
4. 运行完整测试
5. 创建 Git 标签
6. 部署到生产环境
7. 发布公告

## 社区准则

### 行为准则

我们致力于为每个人提供友好、安全和欢迎的环境，无论：

- 性别、性别认同和表达
- 性取向
- 残疾
- 外貌
- 身体大小
- 种族
- 年龄
- 宗教
- 技术选择

### 预期行为

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不当行为

- 使用性化的语言或图像
- 人身攻击或政治攻击
- 公开或私下骚扰
- 未经许可发布他人私人信息
- 其他在专业环境中不当的行为

## 获得帮助

如果您需要帮助或有任何问题，可以通过以下方式联系我们：

- 创建 GitHub Issue
- 发送邮件到项目维护者
- 加入项目讨论群

## 致谢

感谢所有为这个项目做出贡献的人！您的努力让这个项目变得更好。

---

再次感谢您的贡献！🎉