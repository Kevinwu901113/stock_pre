#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票涨跌预测脚本
功能：使用训练好的模型预测股票次日开盘涨跌
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from typing import List, Dict

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_predictor import MLPredictor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_stock_list(file_path: str) -> List[str]:
    """从文件加载股票列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stocks = [line.strip() for line in f if line.strip()]
        return stocks
    except Exception as e:
        logger.error(f"加载股票列表失败: {e}")
        return []

def save_predictions(predictions: Dict[str, float], output_file: str):
    """保存预测结果"""
    try:
        # 准备输出数据
        output_data = {
            'prediction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(predictions),
            'predictions': []
        }
        
        for stock_code, prob in predictions.items():
            output_data['predictions'].append({
                'stock_code': stock_code,
                'up_probability': prob,
                'prediction': '看涨' if prob > 0.5 else '看跌',
                'confidence': 'high' if abs(prob - 0.5) > 0.2 else 'medium' if abs(prob - 0.5) > 0.1 else 'low'
            })
        
        # 保存为JSON格式
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"预测结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"保存预测结果失败: {e}")

def print_top_predictions(predictions: Dict[str, float], top_n: int = 20):
    """打印Top预测结果"""
    print(f"\n=== Top {top_n} 看涨股票 ===")
    print(f"{'股票代码':<10} {'上涨概率':<10} {'预测':<6} {'置信度':<8}")
    print("-" * 40)
    
    sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
    
    for i, (stock_code, prob) in enumerate(sorted_predictions[:top_n]):
        prediction = '看涨' if prob > 0.5 else '看跌'
        confidence = 'high' if abs(prob - 0.5) > 0.2 else 'medium' if abs(prob - 0.5) > 0.1 else 'low'
        print(f"{stock_code:<10} {prob:<10.4f} {prediction:<6} {confidence:<8}")
    
    print(f"\n=== Top {top_n} 看跌股票 ===")
    print(f"{'股票代码':<10} {'上涨概率':<10} {'预测':<6} {'置信度':<8}")
    print("-" * 40)
    
    for i, (stock_code, prob) in enumerate(sorted_predictions[-top_n:]):
        prediction = '看涨' if prob > 0.5 else '看跌'
        confidence = 'high' if abs(prob - 0.5) > 0.2 else 'medium' if abs(prob - 0.5) > 0.1 else 'low'
        print(f"{stock_code:<10} {prob:<10.4f} {prediction:<6} {confidence:<8}")

def main():
    parser = argparse.ArgumentParser(description='预测股票次日开盘涨跌')
    parser.add_argument('--stocks', type=str, nargs='+',
                       help='指定股票代码列表，如: --stocks 000001 000002 600000')
    parser.add_argument('--stock_file', type=str,
                       help='包含股票代码的文件路径，每行一个股票代码')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='配置文件路径')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径，默认不保存文件')
    parser.add_argument('--top_n', type=int, default=20,
                       help='显示Top N的预测结果')
    parser.add_argument('--all_stocks', action='store_true',
                       help='预测所有股票池中的股票')
    
    args = parser.parse_args()
    
    try:
        logger.info("开始股票涨跌预测...")
        
        # 初始化预测器
        predictor = MLPredictor(config_path=args.config)
        
        # 确定要预测的股票列表
        stock_codes = None
        
        if args.stocks:
            stock_codes = args.stocks
            logger.info(f"预测指定股票: {stock_codes}")
        elif args.stock_file:
            stock_codes = load_stock_list(args.stock_file)
            logger.info(f"从文件加载股票列表: {len(stock_codes)} 只股票")
        elif args.all_stocks:
            logger.info("预测所有股票池中的股票")
        else:
            # 默认预测一些热门股票
            stock_codes = [
                '000001', '000002', '000858', '000876', '002415',
                '600000', '600036', '600519', '600887', '601318',
                '601398', '601857', '601988', '603259', '688981'
            ]
            logger.info(f"使用默认股票列表: {len(stock_codes)} 只股票")
        
        # 进行预测
        logger.info("正在预测...")
        predictions = predictor.predict_today_updown(stock_codes)
        
        if not predictions:
            logger.warning("没有获得任何预测结果")
            return
        
        logger.info(f"预测完成，成功预测 {len(predictions)} 只股票")
        
        # 统计信息
        up_count = sum(1 for prob in predictions.values() if prob > 0.5)
        down_count = len(predictions) - up_count
        avg_prob = sum(predictions.values()) / len(predictions)
        
        print(f"\n=== 预测统计 ===")
        print(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总股票数: {len(predictions)}")
        print(f"看涨股票: {up_count} ({up_count/len(predictions)*100:.1f}%)")
        print(f"看跌股票: {down_count} ({down_count/len(predictions)*100:.1f}%)")
        print(f"平均上涨概率: {avg_prob:.4f}")
        
        # 显示Top预测结果
        print_top_predictions(predictions, args.top_n)
        
        # 保存结果
        if args.output:
            save_predictions(predictions, args.output)
        
        # 高置信度推荐
        high_confidence_up = [(code, prob) for code, prob in predictions.items() 
                             if prob > 0.7]
        high_confidence_down = [(code, prob) for code, prob in predictions.items() 
                               if prob < 0.3]
        
        if high_confidence_up:
            print(f"\n=== 高置信度看涨推荐 (概率>0.7) ===")
            for code, prob in sorted(high_confidence_up, key=lambda x: x[1], reverse=True):
                print(f"{code}: {prob:.4f}")
        
        if high_confidence_down:
            print(f"\n=== 高置信度看跌警告 (概率<0.3) ===")
            for code, prob in sorted(high_confidence_down, key=lambda x: x[1]):
                print(f"{code}: {prob:.4f}")
        
        print("\n预测完成！")
        
    except Exception as e:
        logger.error(f"预测过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()