#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测脚本

使用训练好的机器学习模型对股票进行预测

使用方法:
python predict_stocks.py --model logistic_regression
python predict_stocks.py --model xgboost --stock_codes 000001,000002
python predict_stocks.py --model random_forest --top_n 20
"""

import sys
import os
import argparse
import logging
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ai.strategy_analyzer import StrategyAnalyzer
from backend.app.core.config import settings
from backend.app.core.database import init_db, get_db
from backend.app.models.stock import Stock, Recommendation, RecommendationType, StrategyType


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/predict_stocks.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def get_active_stocks(limit: int = 100) -> List[str]:
    """获取活跃股票代码列表"""
    try:
        db = next(get_db())
        stocks = db.query(Stock).filter(
            Stock.is_active == True,
            ~Stock.name.like('%ST%'),
            ~Stock.name.like('%退%')
        ).limit(limit).all()
        
        return [stock.code for stock in stocks]
    except Exception as e:
        logging.error(f"获取股票列表失败: {e}")
        return []
    finally:
        db.close()


def save_predictions_to_db(predictions: List[Dict[str, Any]], model_name: str):
    """保存预测结果到数据库"""
    try:
        db = next(get_db())
        
        for pred in predictions:
            if pred['prediction'] == 1:  # 只保存买入推荐
                recommendation = Recommendation(
                    stock_code=pred['stock_code'],
                    recommendation_type=RecommendationType.BUY,
                    strategy_type=StrategyType.ML_MODEL,
                    confidence=pred['confidence'],
                    target_price=None,  # ML模型暂不预测目标价格
                    stop_loss_price=None,
                    expected_return=None,
                    reason=f"机器学习模型{model_name}预测买入信号，置信度{pred['confidence']:.2%}",
                    created_at=datetime.now()
                )
                
                db.add(recommendation)
        
        db.commit()
        logging.info(f"保存了{len([p for p in predictions if p['prediction'] == 1])}条买入推荐到数据库")
        
    except Exception as e:
        logging.error(f"保存预测结果失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='使用机器学习模型预测股票')
    parser.add_argument('--model', type=str, required=True,
                       choices=['logistic_regression', 'random_forest', 'xgboost'],
                       help='模型名称')
    parser.add_argument('--stock_codes', type=str, default='',
                       help='指定股票代码，用逗号分隔，如: 000001,000002')
    parser.add_argument('--top_n', type=int, default=50,
                       help='预测前N只活跃股票')
    parser.add_argument('--min_confidence', type=float, default=0.6,
                       help='最小置信度阈值')
    parser.add_argument('--save_to_db', action='store_true',
                       help='是否保存预测结果到数据库')
    parser.add_argument('--output_file', type=str, default='',
                       help='输出结果到CSV文件')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    try:
        logger.info("开始股票预测")
        logger.info(f"使用模型: {args.model}")
        logger.info(f"最小置信度: {args.min_confidence}")
        
        # 初始化数据库
        init_db()
        
        # 创建策略分析器
        analyzer = StrategyAnalyzer()
        
        # 确定要预测的股票
        if args.stock_codes:
            stock_codes = [code.strip() for code in args.stock_codes.split(',')]
            logger.info(f"预测指定股票: {stock_codes}")
        else:
            stock_codes = get_active_stocks(args.top_n)
            logger.info(f"预测前{args.top_n}只活跃股票")
        
        if not stock_codes:
            logger.error("没有找到要预测的股票")
            return
        
        # 进行预测
        predictions = []
        successful_predictions = 0
        
        for i, stock_code in enumerate(stock_codes, 1):
            logger.info(f"预测进度: {i}/{len(stock_codes)} - {stock_code}")
            
            try:
                result = analyzer.predict_stock(args.model, stock_code)
                
                if result:
                    predictions.append(result)
                    successful_predictions += 1
                    
                    if result['prediction'] == 1 and result['confidence'] >= args.min_confidence:
                        logger.info(f"✅ {stock_code}: 买入信号, 置信度: {result['confidence']:.2%}")
                    elif result['prediction'] == 1:
                        logger.info(f"⚠️ {stock_code}: 买入信号(低置信度), 置信度: {result['confidence']:.2%}")
                    else:
                        logger.debug(f"❌ {stock_code}: 不买入, 置信度: {result['confidence']:.2%}")
                else:
                    logger.warning(f"⚠️ {stock_code}: 预测失败")
                    
            except Exception as e:
                logger.error(f"预测股票{stock_code}时出错: {e}")
                continue
        
        logger.info(f"预测完成: {successful_predictions}/{len(stock_codes)} 成功")
        
        # 过滤高置信度的买入信号
        buy_signals = [
            p for p in predictions 
            if p['prediction'] == 1 and p['confidence'] >= args.min_confidence
        ]
        
        # 按置信度排序
        buy_signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 输出结果
        logger.info("=" * 60)
        logger.info(f"高置信度买入信号 (置信度 >= {args.min_confidence})")
        logger.info("=" * 60)
        
        if buy_signals:
            for signal in buy_signals:
                logger.info(f"{signal['stock_code']}: 置信度 {signal['confidence']:.2%}, "
                           f"买入概率 {signal['buy_probability']:.2%}")
        else:
            logger.info("没有找到高置信度的买入信号")
        
        # 统计信息
        total_buy_signals = len([p for p in predictions if p['prediction'] == 1])
        logger.info("\n统计信息:")
        logger.info(f"总预测数: {len(predictions)}")
        logger.info(f"买入信号数: {total_buy_signals}")
        logger.info(f"高置信度买入信号数: {len(buy_signals)}")
        logger.info(f"买入信号比例: {total_buy_signals/len(predictions)*100:.1f}%" if predictions else "0%")
        
        # 保存到数据库
        if args.save_to_db and buy_signals:
            save_predictions_to_db(buy_signals, args.model)
        
        # 保存到CSV文件
        if args.output_file and predictions:
            df = pd.DataFrame(predictions)
            df['prediction_date'] = df['prediction_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df.to_csv(args.output_file, index=False, encoding='utf-8-sig')
            logger.info(f"预测结果已保存到: {args.output_file}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"预测过程出错: {e}")
        raise


if __name__ == "__main__":
    main()