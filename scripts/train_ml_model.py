#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习模型训练脚本

用于训练股票预测模型，支持多种算法：
- 逻辑回归 (Logistic Regression)
- 随机森林 (Random Forest)
- XGBoost

使用方法:
python train_ml_model.py --model logistic_regression
python train_ml_model.py --model random_forest --test_size 0.3
python train_ml_model.py --model xgboost --target_return 0.03
"""

import sys
import os
import argparse
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ai.strategy_analyzer import StrategyAnalyzer
from backend.app.core.config import settings
from backend.app.core.database import init_db


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/train_model.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='训练股票预测模型')
    parser.add_argument('--model', type=str, default='logistic_regression',
                       choices=['logistic_regression', 'random_forest', 'xgboost'],
                       help='模型类型')
    parser.add_argument('--test_size', type=float, default=0.2,
                       help='测试集比例 (0.1-0.5)')
    parser.add_argument('--target_return', type=float, default=0.02,
                       help='目标收益率阈值')
    parser.add_argument('--days', type=int, default=730,
                       help='训练数据天数')
    parser.add_argument('--min_samples', type=int, default=1000,
                       help='最小样本数')
    
    args = parser.parse_args()
    
    # 验证参数
    if not 0.1 <= args.test_size <= 0.5:
        print("错误: test_size 必须在 0.1 到 0.5 之间")
        return
    
    if not 0.005 <= args.target_return <= 0.1:
        print("错误: target_return 必须在 0.005 到 0.1 之间")
        return
    
    # 设置日志
    logger = setup_logging()
    
    try:
        logger.info("开始训练模型")
        logger.info(f"模型类型: {args.model}")
        logger.info(f"测试集比例: {args.test_size}")
        logger.info(f"目标收益率: {args.target_return}")
        logger.info(f"训练数据天数: {args.days}")
        
        # 初始化数据库
        init_db()
        
        # 创建策略分析器
        analyzer = StrategyAnalyzer()
        
        # 训练模型
        results = analyzer.train_model(
            model_name=args.model,
            test_size=args.test_size
        )
        
        if not results:
            logger.error("模型训练失败")
            return
        
        # 输出结果
        logger.info("=" * 50)
        logger.info("模型训练完成")
        logger.info("=" * 50)
        logger.info(f"模型名称: {results['model_name']}")
        logger.info(f"训练样本数: {results['train_samples']}")
        logger.info(f"测试样本数: {results['test_samples']}")
        logger.info(f"AUC分数: {results['auc_score']:.4f}")
        logger.info(f"交叉验证均值: {results['cv_mean']:.4f}")
        logger.info(f"交叉验证标准差: {results['cv_std']:.4f}")
        logger.info(f"模型文件: {results['model_file']}")
        logger.info(f"特征文件: {results['feature_names_file']}")
        
        print("\n分类报告:")
        print(results['classification_report'])
        
        print("\n混淆矩阵:")
        confusion_matrix = results['confusion_matrix']
        print(f"真负例: {confusion_matrix[0][0]}, 假正例: {confusion_matrix[0][1]}")
        print(f"假负例: {confusion_matrix[1][0]}, 真正例: {confusion_matrix[1][1]}")
        
        # 计算其他指标
        tn, fp, fn, tp = confusion_matrix[0][0], confusion_matrix[0][1], confusion_matrix[1][0], confusion_matrix[1][1]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        logger.info(f"精确率: {precision:.4f}")
        logger.info(f"召回率: {recall:.4f}")
        logger.info(f"F1分数: {f1_score:.4f}")
        
        # 模型评估建议
        if results['auc_score'] >= 0.7:
            logger.info("✅ 模型性能良好，可以用于生产环境")
        elif results['auc_score'] >= 0.6:
            logger.info("⚠️ 模型性能一般，建议优化特征或调整参数")
        else:
            logger.info("❌ 模型性能较差，需要重新设计特征或策略")
        
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"训练过程出错: {e}")
        raise


if __name__ == "__main__":
    main()