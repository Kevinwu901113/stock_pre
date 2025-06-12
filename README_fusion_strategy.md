# 推荐系统融合策略

## 概述

本项目实现了一个完整的股票推荐系统融合策略，将机器学习模型预测的上涨概率与多因子线性打分结果进行智能融合，提供多种融合方法和统一的JSON输出格式。

## 核心功能

### 1. 增强版融合策略 (EnhancedFusionStrategy)

位于 `enhanced_fusion_strategy.py`，提供以下融合方法：

- **加权平均** (`weighted_average`): 对ML概率和因子得分进行加权平均
- **优先过滤** (`filter_first`): 先用ML模型过滤，再按因子得分排序
- **排序微调** (`rank_adjustment`): 基于因子得分排序，用ML预测进行微调
- **动态权重** (`dynamic_weight`): 根据预测置信度动态调整权重
- **一致性增强** (`consensus_boost`): 对ML和因子模型一致看涨的股票给予额外加分

### 2. 统一输出格式

所有融合方法输出统一的JSON格式，包含：

```json
{
  "method": "融合方法名称",
  "timestamp": "生成时间",
  "config": {
    "ml_weight": 0.6,
    "factor_weight": 0.4,
    "ml_threshold": 0.5,
    "factor_threshold": 0.0
  },
  "recommendations": [
    {
      "rank": 1,
      "stock_code": "000001",
      "stock_name": "平安银行",
      "final_score": 0.85,
      "ml_probability": 0.75,
      "factor_score": 0.68,
      "confidence_level": "high",
      "reason": "ML模型和因子模型均看涨，一致性强",
      "details": {
        "ml_prediction": "上涨",
        "factor_rank": 5,
        "consensus": true
      }
    }
  ],
  "summary": {
    "total_stocks": 100,
    "recommended_count": 10,
    "consensus_ratio": 0.7,
    "avg_ml_probability": 0.68,
    "avg_factor_score": 0.45
  }
}
```

## 配置文件

### fusion_config.yaml

包含所有融合策略的配置参数：

```yaml
fusion_methods:
  weighted_average:
    ml_weight: 0.6
    factor_weight: 0.4
    ml_threshold: 0.5
    factor_threshold: 0.0
  
  consensus_boost:
    base_ml_weight: 0.5
    base_factor_weight: 0.5
    consensus_bonus: 0.2
    ml_threshold: 0.6
    factor_threshold: 0.1

risk_control:
  max_recommendations: 20
  min_recommendations: 5
  sector_diversification: true
  liquidity_requirement: 1000000
  volatility_limit: 0.05
```

## 使用方法

### 1. 基本使用

```python
from enhanced_fusion_strategy import EnhancedFusionStrategy, FusionMethod

# 初始化融合策略
fusion = EnhancedFusionStrategy()

# 运行一致性增强融合
results = fusion.run_fusion(
    method=FusionMethod.CONSENSUS_BOOST,
    top_n=10,
    save_results=True
)

# 输出结果
print(f"推荐股票数量: {len(results['recommendations'])}")
for rec in results['recommendations'][:5]:
    print(f"{rec['rank']}. {rec['stock_name']} - 得分: {rec['final_score']:.3f}")
```

### 2. 运行示例脚本

```bash
# 运行完整示例
python run_fusion_example.py

# 运行特定融合方法
python -c "from run_fusion_example import run_enhanced_fusion_strategy; run_enhanced_fusion_strategy('consensus_boost', 10)"
```

### 3. 比较不同方法

```python
from run_fusion_example import compare_fusion_methods

# 比较多种融合方法
compare_fusion_methods([
    "weighted_average", 
    "filter_first", 
    "consensus_boost"
], top_n=10)
```

## 输出文件

所有结果保存在 `results/` 目录下：

- `fusion_results_[method]_[timestamp].json`: 融合推荐结果
- `fusion_comparison_[timestamp].json`: 方法比较结果
- `consensus_analysis_[timestamp].json`: 一致性分析结果
- `fusion_recommendation.log`: 运行日志

## 核心优势

1. **多种融合策略**: 提供5种不同的融合方法，适应不同场景
2. **统一输出格式**: 所有方法输出标准化JSON格式，便于集成
3. **详细推荐理由**: 每个推荐都包含详细的推荐理由和置信度
4. **风险控制**: 内置风险控制机制，确保推荐质量
5. **可配置性**: 通过YAML配置文件灵活调整参数
6. **一致性分析**: 分析ML模型和因子模型的一致性
7. **性能监控**: 提供详细的性能指标和统计信息

## 技术特点

- **模块化设计**: 各组件独立，易于维护和扩展
- **类型安全**: 使用枚举类型确保方法名称正确
- **异常处理**: 完善的错误处理和日志记录
- **性能优化**: 高效的数据处理和计算
- **可扩展性**: 易于添加新的融合方法

## 依赖要求

- Python 3.7+
- pandas
- numpy
- PyYAML
- 现有的ML预测器和因子打分引擎

## 快速开始

1. 确保所有依赖模块正常工作
2. 检查配置文件 `fusion_config.yaml`
3. 运行示例脚本: `python run_fusion_example.py`
4. 查看 `results/` 目录下的输出文件

## 注意事项

- 首次运行前请确保ML模型已训练完成
- 配置文件中的阈值需要根据实际数据调整
- 建议定期评估和调整融合策略参数
- 生产环境使用前请充分测试各种边界情况