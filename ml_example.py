#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习模块使用示例
展示如何训练模型和进行预测
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_predictor import MLPredictor
from main import StockRecommendationSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def example_train_model():
    """示例：训练机器学习模型"""
    print("=== 机器学习模型训练示例 ===")
    
    # 初始化预测器
    predictor = MLPredictor()
    
    # 设置训练数据日期范围（使用较小的数据集进行快速演示）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"训练数据日期范围: {start_date} 到 {end_date}")
    
    try:
        # 生成训练样本（限制股票数量以加快演示速度）
        print("正在生成训练样本...")
        
        # 使用少量股票进行快速演示
        demo_stocks = [
            '000001', '000002', '000858', '000876', '002415',
            '600000', '600036', '600519', '600887', '601318'
        ]
        
        features, labels = predictor.generate_training_samples(
            start_date=start_date,
            end_date=end_date,
            stock_codes=demo_stocks,  # 限制股票数量
            min_samples_per_stock=20
        )
        
        print(f"训练样本统计:")
        print(f"  - 总样本数: {len(features)}")
        print(f"  - 特征数量: {len(features.columns)}")
        print(f"  - 正样本比例: {labels.mean():.3f}")
        
        # 训练模型
        print("\n开始训练模型...")
        result = predictor.train_model(
            features=features,
            labels=labels,
            n_splits=3  # 减少交叉验证折数以加快速度
        )
        
        # 输出训练结果
        print("\n=== 训练结果 ===")
        avg_scores = result['avg_scores']
        for metric in ['auc', 'accuracy', 'precision', 'recall', 'f1']:
            mean_val = avg_scores[f'avg_{metric}']
            std_val = avg_scores[f'std_{metric}']
            print(f"{metric.upper()}: {mean_val:.4f} ± {std_val:.4f}")
        
        # 输出特征重要性前5
        print("\n=== 特征重要性 Top 5 ===")
        top_features = result['feature_importance'].head(5)
        for _, row in top_features.iterrows():
            print(f"{row['feature']}: {row['importance']:.2f}")
        
        print("\n模型训练完成！")
        return True
        
    except Exception as e:
        print(f"训练失败: {e}")
        return False

def example_predict_stocks():
    """示例：使用模型预测股票"""
    print("\n=== 股票预测示例 ===")
    
    # 初始化预测器
    predictor = MLPredictor()
    
    # 检查模型是否存在
    if not predictor.load_model():
        print("模型未找到，请先训练模型")
        return False
    
    try:
        # 预测一些热门股票
        test_stocks = [
            '000001',  # 平安银行
            '000002',  # 万科A
            '600000',  # 浦发银行
            '600036',  # 招商银行
            '600519',  # 贵州茅台
        ]
        
        print(f"正在预测 {len(test_stocks)} 只股票...")
        predictions = predictor.predict_today_updown(test_stocks)
        
        if predictions:
            print("\n=== 预测结果 ===")
            print(f"{'股票代码':<10} {'上涨概率':<10} {'预测':<6} {'置信度':<8}")
            print("-" * 40)
            
            for stock_code, prob in predictions.items():
                prediction = '看涨' if prob > 0.5 else '看跌'
                confidence = 'high' if abs(prob - 0.5) > 0.2 else 'medium' if abs(prob - 0.5) > 0.1 else 'low'
                print(f"{stock_code:<10} {prob:<10.4f} {prediction:<6} {confidence:<8}")
            
            # 高置信度推荐
            high_confidence = [(code, prob) for code, prob in predictions.items() 
                             if abs(prob - 0.5) > 0.2]
            
            if high_confidence:
                print("\n=== 高置信度预测 ===")
                for code, prob in sorted(high_confidence, key=lambda x: abs(x[1] - 0.5), reverse=True):
                    direction = '看涨' if prob > 0.5 else '看跌'
                    print(f"{code}: {prob:.4f} ({direction})")
        else:
            print("没有获得预测结果")
            
        return True
        
    except Exception as e:
        print(f"预测失败: {e}")
        return False

def example_integrated_recommendation():
    """示例：集成ML预测的股票推荐"""
    print("\n=== 集成ML预测的推荐示例 ===")
    
    try:
        # 初始化推荐系统
        system = StockRecommendationSystem(
            config_path='config.yaml',
            stock_universe='conservative',  # 使用保守型股票池
            factor_strategy='default',
            time_period='medium_term'
        )
        
        print("正在运行集成ML预测的股票推荐...")
        
        # 运行推荐（会自动包含ML预测）
        results = system.run_recommendation(
            top_n=10,  # 只推荐前10只股票
            save_results=False  # 不保存结果文件
        )
        
        if results:
            print("\n=== 推荐结果（含ML预测） ===")
            print(f"{'排名':<4} {'股票代码':<8} {'股票名称':<12} {'综合得分':<8} {'ML预测':<6} {'ML概率':<8}")
            print("-" * 60)
            
            for result in results:
                rank = result.get('rank', 0)
                code = result.get('stock_code', '')
                name = result.get('stock_name', '')[:10]  # 限制名称长度
                score = result.get('total_score', 0)
                ml_pred = result.get('ml_prediction', '无')
                ml_prob = result.get('ml_up_probability', 0)
                
                ml_prob_str = f"{ml_prob:.3f}" if ml_prob is not None else "N/A"
                
                print(f"{rank:<4} {code:<8} {name:<12} {score:<8.2f} {ml_pred:<6} {ml_prob_str:<8}")
            
            # 统计ML预测一致性
            ml_bullish = sum(1 for r in results if r.get('ml_prediction') == '看涨')
            ml_bearish = sum(1 for r in results if r.get('ml_prediction') == '看跌')
            
            print(f"\n=== ML预测统计 ===")
            print(f"看涨: {ml_bullish}, 看跌: {ml_bearish}")
            
            # 高一致性推荐（技术面和ML都看涨）
            high_consensus = [r for r in results 
                            if r.get('total_score', 0) > 0 and r.get('ml_prediction') == '看涨']
            
            if high_consensus:
                print(f"\n=== 高一致性推荐（技术面+ML双重看涨） ===")
                for result in high_consensus:
                    print(f"{result['stock_name']}({result['stock_code']}): "
                          f"技术得分{result['total_score']:.2f}, "
                          f"ML概率{result['ml_up_probability']:.3f}")
        else:
            print("没有生成推荐结果")
            
        return True
        
    except Exception as e:
        print(f"集成推荐失败: {e}")
        return False

def main():
    """主函数"""
    print("股票推荐系统 - 机器学习模块示例")
    print("=" * 50)
    
    # 示例1: 训练模型
    print("\n1. 训练机器学习模型")
    train_success = example_train_model()
    
    if train_success:
        # 示例2: 预测股票
        print("\n2. 使用模型预测股票")
        example_predict_stocks()
        
        # 示例3: 集成推荐
        print("\n3. 集成ML预测的股票推荐")
        example_integrated_recommendation()
    else:
        print("\n由于模型训练失败，跳过后续示例")
    
    print("\n=== 示例完成 ===")
    print("\n使用说明:")
    print("1. 训练模型: python train_ml_model.py")
    print("2. 预测股票: python predict_stocks.py")
    print("3. 集成推荐: python main.py")

if __name__ == "__main__":
    main()