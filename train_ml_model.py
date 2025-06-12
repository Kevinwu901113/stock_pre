#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习模型训练脚本
功能：训练LightGBM模型并评估性能
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_predictor import MLPredictor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='训练股票涨跌预测模型')
    parser.add_argument('--start_date', type=str, default=None,
                       help='训练数据开始日期 (YYYY-MM-DD)，默认为2年前')
    parser.add_argument('--end_date', type=str, default=None,
                       help='训练数据结束日期 (YYYY-MM-DD)，默认为今天')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='配置文件路径')
    parser.add_argument('--test_size', type=float, default=0.2,
                       help='测试集比例')
    parser.add_argument('--cv_folds', type=int, default=5,
                       help='交叉验证折数')
    parser.add_argument('--predict_sample', action='store_true',
                       help='训练完成后进行样本预测测试')
    
    args = parser.parse_args()
    
    try:
        logger.info("开始训练机器学习模型...")
        
        # 初始化预测器
        predictor = MLPredictor(config_path=args.config)
        
        # 设置日期范围
        end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
        start_date = args.start_date or (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
        
        logger.info(f"训练数据日期范围: {start_date} 到 {end_date}")
        
        # 生成训练样本
        logger.info("生成训练样本...")
        features, labels = predictor.generate_training_samples(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"训练样本统计:")
        logger.info(f"  - 总样本数: {len(features)}")
        logger.info(f"  - 特征数量: {len(features.columns) - 1}")
        logger.info(f"  - 正样本比例: {labels.mean():.3f}")
        logger.info(f"  - 股票数量: {features['stock_code'].nunique()}")
        
        # 训练模型
        logger.info("开始训练模型...")
        result = predictor.train_model(
            features=features,
            labels=labels,
            test_size=args.test_size,
            n_splits=args.cv_folds
        )
        
        # 输出训练结果
        logger.info("\n=== 训练结果 ===")
        avg_scores = result['avg_scores']
        for metric in ['auc', 'accuracy', 'precision', 'recall', 'f1']:
            mean_val = avg_scores[f'avg_{metric}']
            std_val = avg_scores[f'std_{metric}']
            logger.info(f"{metric.upper()}: {mean_val:.4f} ± {std_val:.4f}")
        
        # 输出特征重要性前10
        logger.info("\n=== 特征重要性 Top 10 ===")
        top_features = result['feature_importance'].head(10)
        for _, row in top_features.iterrows():
            logger.info(f"{row['feature']}: {row['importance']:.2f}")
        
        # 样本预测测试
        if args.predict_sample:
            logger.info("\n=== 样本预测测试 ===")
            test_stocks = ['000001', '000002', '600000', '600036', '000858']
            predictions = predictor.predict_today_updown(test_stocks)
            
            logger.info("预测结果:")
            for stock_code, prob in predictions.items():
                logger.info(f"{stock_code}: {prob:.4f} ({'看涨' if prob > 0.5 else '看跌'})")
        
        logger.info("\n模型训练完成！")
        logger.info(f"模型文件已保存到: {predictor.model_path}")
        
    except Exception as e:
        logger.error(f"训练过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()