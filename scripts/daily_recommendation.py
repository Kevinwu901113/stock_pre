#!/usr/bin/env python3
"""
每日推荐生成脚本

每天定时执行，获取最新数据并生成股票推荐。
适合在收盘后运行，为次日开盘提供投资建议。
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_db
from config.settings import settings
from data.manager import DataManager
from strategies.technical import ComprehensiveTechnicalStrategy
from backend.app.services.recommendation_generator import RecommendationGenerator
from backend.app.core.database import init_db, get_db
from backend.app.models.stock import Stock, StockPrice, Recommendation, RecommendationType, StrategyType
from data_sources.tushare_source import TushareSource
from ai.strategy_analyzer import StrategyAnalyzer
from sqlalchemy.orm import Session


class DailyRecommendationGenerator:
    """每日推荐生成器"""
    
    def __init__(self):
        self.logger = logger.bind(module="daily_recommendation")
        self.data_manager = DataManager()
        self.recommendation_generator = RecommendationGenerator()
        
    async def run(self):
        """运行每日推荐生成流程"""
        try:
            self.logger.info("开始每日推荐生成流程")
            
            # 1. 更新股票数据
            await self.update_stock_data()
            
            # 2. 获取活跃股票列表
            stock_codes = await self.get_active_stocks()
            
            # 3. 执行策略分析
            recommendations = await self.generate_recommendations(stock_codes)
            
            # 4. 保存推荐结果
            await self.save_recommendations(recommendations)
            
            # 5. 生成报告
            await self.generate_report(recommendations)
            
            self.logger.info(f"每日推荐生成完成，共生成{len(recommendations)}条推荐")
            
        except Exception as e:
            self.logger.error(f"每日推荐生成失败: {e}")
            raise
    
    async def update_stock_data(self):
        """更新股票数据"""
        try:
            self.logger.info("开始更新股票数据")
            
            # 获取昨日日期（避免当日数据不完整）
            yesterday = date.today() - timedelta(days=1)
            
            # 更新股票基础信息
            await self.data_manager.update_stock_list()
            
            # 更新价格数据
            await self.data_manager.update_daily_data(end_date=yesterday)
            
            self.logger.info("股票数据更新完成")
            
        except Exception as e:
            self.logger.error(f"更新股票数据失败: {e}")
            raise
    
    async def get_active_stocks(self) -> List[str]:
        """获取活跃股票列表"""
        try:
            db = next(get_db())
            
            # 获取活跃股票（排除ST、退市等）
            stocks = db.query(Stock).filter(
                Stock.is_active == True,
                ~Stock.name.like('%ST%'),
                ~Stock.name.like('%退%'),
                Stock.market.in_(['SH', 'SZ'])
            ).all()
            
            stock_codes = [stock.code for stock in stocks]
            
            self.logger.info(f"获取到{len(stock_codes)}只活跃股票")
            return stock_codes
            
        except Exception as e:
            self.logger.error(f"获取活跃股票列表失败: {e}")
            return []
        finally:
            db.close()
    
    async def generate_recommendations(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """生成推荐"""
        try:
            self.logger.info(f"开始为{len(stock_codes)}只股票生成推荐")
            
            db = next(get_db())
            
            # 初始化综合技术策略
            strategy_params = {
                'ma_period': 5,
                'turnover_threshold': 5.0,
                'volume_threshold': 1.5,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'min_confidence': 0.7
            }
            
            strategy = ComprehensiveTechnicalStrategy(db, strategy_params)
            analyzer = StrategyAnalyzer()
            
            # 分批处理股票（避免内存占用过大）
            batch_size = 100
            all_recommendations = []
            ml_recommendations_count = 0
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i + batch_size]
                self.logger.info(f"处理第{i//batch_size + 1}批股票，共{len(batch_codes)}只")
                
                # 执行技术分析策略
                batch_results = await strategy.execute(batch_codes)
                
                # 为每个推荐生成详细理由
                for result in batch_results:
                    try:
                        # 获取股票信息
                        stock_info = await strategy.get_stock_info(result['stock_code'])
                        
                        # 生成AI推荐理由
                        enhanced_reason = await self.recommendation_generator.generate_recommendation_reason(
                            stock_data=stock_info,
                            strategy_result=result,
                            analysis_type='technical'
                        )
                        
                        # 合并推荐信息
                        recommendation = {
                            **result,
                            'stock_name': stock_info.get('name', '') if stock_info else '',
                            'enhanced_reason': enhanced_reason.get('reason', result['reason']),
                            'risk_assessment': enhanced_reason.get('risk_assessment', 'medium'),
                            'market_context': enhanced_reason.get('market_context', ''),
                            'strategy_name': 'ComprehensiveTechnical',
                            'signal_type': 'end_of_day_buy',
                            'created_at': datetime.now(),
                            'expires_at': datetime.now() + timedelta(days=3)  # 3天有效期
                        }
                        
                        all_recommendations.append(recommendation)
                        
                    except Exception as e:
                        self.logger.error(f"处理股票{result['stock_code']}推荐时出错: {e}")
                        continue
                
                # 尝试机器学习模型预测（如果模型可用）
                for stock_code in batch_codes:
                    try:
                        # 尝试加载逻辑回归模型
                        if analyzer.load_model('logistic_regression'):
                            ml_result = analyzer.predict_stock('logistic_regression', stock_code)
                            
                            if (ml_result and ml_result['prediction'] == 1 and 
                                ml_result['confidence'] >= 0.65):  # 较高置信度阈值
                                
                                # 获取股票信息
                                stock_info = await strategy.get_stock_info(stock_code)
                                
                                # 生成ML推荐理由
                                ml_enhanced_reason = await self.recommendation_generator.generate_recommendation_reason(
                                    stock_data=stock_info,
                                    strategy_result={
                                        'model_name': ml_result['model_name'],
                                        'confidence': ml_result['confidence'],
                                        'buy_probability': ml_result['buy_probability']
                                    },
                                    analysis_type='ml_model'
                                )
                                
                                # 创建ML推荐记录
                                ml_recommendation = {
                                    'stock_code': stock_code,
                                    'stock_name': stock_info.get('name', '') if stock_info else '',
                                    'signal': 'BUY',
                                    'confidence': ml_result['confidence'],
                                    'target_price': None,  # ML模型暂不预测价格
                                    'stop_loss': None,
                                    'expected_return': None,
                                    'reason': ml_enhanced_reason.get('reason', f"机器学习模型预测买入信号，置信度: {ml_result['confidence']:.1%}"),
                                    'enhanced_reason': ml_enhanced_reason.get('reason', ''),
                                    'risk_assessment': ml_enhanced_reason.get('risk_assessment', 'medium'),
                                    'market_context': ml_enhanced_reason.get('market_context', ''),
                                    'strategy_name': 'MLLogisticRegression',
                                    'signal_type': 'ml_prediction',
                                    'created_at': datetime.now(),
                                    'expires_at': datetime.now() + timedelta(days=3)
                                }
                                
                                all_recommendations.append(ml_recommendation)
                                ml_recommendations_count += 1
                                
                                self.logger.info(f"ML模型推荐: {stock_code} (置信度: {ml_result['confidence']:.2%})")
                                
                    except Exception as ml_e:
                        self.logger.debug(f"ML预测失败 {stock_code}: {ml_e}")
                        pass  # ML预测失败不影响技术分析
            
            self.logger.info(f"推荐生成完成，技术分析: {len(all_recommendations) - ml_recommendations_count}条，ML模型: {ml_recommendations_count}条")
            return all_recommendations
            
        except Exception as e:
            self.logger.error(f"生成推荐失败: {e}")
            return []
        finally:
            db.close()
    
    async def save_recommendations(self, recommendations: List[Dict[str, Any]]):
        """保存推荐到数据库"""
        try:
            if not recommendations:
                self.logger.info("没有推荐需要保存")
                return
            
            db = next(get_db())
            
            # 清理过期推荐
            db.query(Recommendation).filter(
                Recommendation.expires_at < datetime.now()
            ).update({'is_active': False})
            
            # 保存新推荐
            saved_count = 0
            for rec in recommendations:
                try:
                    db_recommendation = Recommendation(
                        stock_code=rec['stock_code'],
                        recommendation_type=rec['signal'],
                        strategy_name=rec['strategy_name'],
                        confidence_score=rec['confidence'],
                        target_price=rec.get('target_price'),
                        stop_loss_price=rec.get('stop_loss'),
                        reason=rec['enhanced_reason'],
                        signal_type=rec['signal_type'],
                        expected_return=rec.get('expected_return'),
                        holding_period=rec.get('holding_period'),
                        risk_level=rec.get('risk_assessment', 'medium'),
                        created_at=rec['created_at'],
                        expires_at=rec['expires_at'],
                        is_active=True
                    )
                    
                    db.add(db_recommendation)
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.error(f"保存推荐{rec['stock_code']}失败: {e}")
                    continue
            
            db.commit()
            self.logger.info(f"成功保存{saved_count}条推荐到数据库")
            
        except Exception as e:
            self.logger.error(f"保存推荐失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def generate_report(self, recommendations: List[Dict[str, Any]]):
        """生成推荐报告"""
        try:
            if not recommendations:
                return
            
            # 统计信息
            total_count = len(recommendations)
            high_confidence = len([r for r in recommendations if r['confidence'] >= 0.8])
            avg_confidence = sum(r['confidence'] for r in recommendations) / total_count
            avg_expected_return = sum(r.get('expected_return', 0) for r in recommendations) / total_count
            
            # 按置信度排序
            top_recommendations = sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:10]
            
            # 生成报告内容
            report_content = f"""
# 每日股票推荐报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 推荐概览

- **推荐总数**: {total_count}
- **高置信度推荐** (≥80%): {high_confidence}
- **平均置信度**: {avg_confidence:.1%}
- **平均预期收益**: {avg_expected_return:.1%}

## 前10推荐股票

| 排名 | 股票代码 | 股票名称 | 置信度 | 预期收益 | 目标价格 | 推荐理由 |
|------|----------|----------|--------|----------|----------|----------|
"""
            
            for i, rec in enumerate(top_recommendations, 1):
                report_content += f"| {i} | {rec['stock_code']} | {rec.get('stock_name', '')} | {rec['confidence']:.1%} | {rec.get('expected_return', 0):.1%} | {rec.get('target_price', 0):.2f} | {rec['reason'][:50]}... |\n"
            
            # 保存报告
            report_file = f"reports/daily_recommendation_{date.today().strftime('%Y%m%d')}.md"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"推荐报告已保存到: {report_file}")
            
        except Exception as e:
            self.logger.error(f"生成推荐报告失败: {e}")


async def main():
    """主函数"""
    # 配置日志
    logger.add(
        f"logs/daily_recommendation_{date.today().strftime('%Y%m%d')}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    try:
        generator = DailyRecommendationGenerator()
        await generator.run()
        
    except Exception as e:
        logger.error(f"每日推荐生成失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())