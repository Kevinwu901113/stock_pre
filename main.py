#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票推荐系统主程序
整合数据获取、特征提取、评分引擎和结果输出模块
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import DataFetcher
from feature_extractor import FeatureExtractor
from scoring_engine import ScoringEngine
from result_writer import ResultWriter
from ml_predictor import MLPredictor

class StockRecommendationSystem:
    """股票推荐系统主类"""
    
    def __init__(self, config_path: str = 'config.yaml', 
                 stock_universe: str = 'default',
                 factor_strategy: str = 'default',
                 time_period: str = 'default'):
        """
        初始化股票推荐系统
        
        Args:
            config_path: 配置文件路径
            stock_universe: 股票池策略 (default, conservative, aggressive)
            factor_strategy: 因子策略 (default, momentum_focused, capital_flow_focused, conservative)
            time_period: 时间周期 (short_term, medium_term, long_term)
        """
        self.config_path = config_path
        self.stock_universe = stock_universe
        self.factor_strategy = factor_strategy
        self.time_period = time_period
        self.config = self._load_config()
        
        # 初始化各个模块，传入策略参数
        self.data_fetcher = DataFetcher(config_path, stock_universe, time_period)
        self.feature_extractor = FeatureExtractor(config_path, factor_strategy, time_period)
        self.scoring_engine = ScoringEngine(config_path, factor_strategy, stock_universe)
        self.result_writer = ResultWriter(config_path)
        self.ml_predictor = MLPredictor(config_path)  # 机器学习预测器
        # self.sell_decision = SellDecision(config_path)  # 注释掉未定义的模块
        
        # 设置日志
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("股票推荐系统初始化完成")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stock_recommendation.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_recommendation(self, 
                          top_n: int = 20,
                          save_results: bool = True,
                          export_excel: bool = False) -> List[Dict]:
        """
        运行完整的股票推荐流程
        
        Args:
            top_n: 推荐股票数量
            save_results: 是否保存结果到文件
            export_excel: 是否导出Excel文件
            
        Returns:
            推荐结果列表
        """
        try:
            self.logger.info(f"开始运行股票推荐系统 - 股票池: {self.stock_universe}, 因子策略: {self.factor_strategy}, 时间周期: {self.time_period}")
            
            # 1. 获取股票数据
            self.logger.info("步骤1: 获取股票数据")
            stock_list = self.data_fetcher.get_stock_list()
            self.logger.info(f"获取到{len(stock_list)}只股票")
            
            # 过滤股票池
            filtered_stocks = self.data_fetcher.filter_stock_universe(stock_list)
            self.logger.info(f"过滤后剩余{len(filtered_stocks)}只股票")
            
            # 获取所有数据
            all_data = self.data_fetcher.get_all_data(filtered_stocks)
            self.logger.info(f"成功获取{len(all_data)}只股票的完整数据")
            
            # 2. 特征提取
            self.logger.info("步骤2: 提取股票特征")
            all_features = self.feature_extractor.batch_extract_features(all_data)
            self.logger.info(f"成功提取{len(all_features)}只股票的特征")
            
            # 3. 股票评分
            self.logger.info("步骤3: 股票评分和排序")
            scored_stocks = self.scoring_engine.score_stocks(all_features)
            
            # 获取Top推荐
            top_recommendations = self.scoring_engine.get_top_recommendations(
                scored_stocks, top_n
            )
            
            # 4. ML预测增强 (可选)
            self.logger.info("步骤4: ML预测增强")
            try:
                # 获取推荐股票的ML预测
                recommended_codes = [stock['stock_code'] for stock in top_recommendations]
                ml_predictions = self.ml_predictor.predict_today_updown(recommended_codes)
                
                # 将ML预测结果添加到推荐中
                for stock in top_recommendations:
                    stock_code = stock['stock_code']
                    if stock_code in ml_predictions:
                        stock['ml_up_probability'] = ml_predictions[stock_code]
                        stock['ml_prediction'] = '看涨' if ml_predictions[stock_code] > 0.5 else '看跌'
                        stock['ml_confidence'] = 'high' if abs(ml_predictions[stock_code] - 0.5) > 0.2 else 'medium'
                    else:
                        stock['ml_up_probability'] = None
                        stock['ml_prediction'] = '无预测'
                        stock['ml_confidence'] = 'none'
                
                self.logger.info(f"ML预测完成，预测了{len(ml_predictions)}只股票")
                
            except Exception as e:
                self.logger.warning(f"ML预测失败，跳过此步骤: {e}")
                # 如果ML预测失败，添加默认值
                for stock in top_recommendations:
                    stock['ml_up_probability'] = None
                    stock['ml_prediction'] = '模型未加载'
                    stock['ml_confidence'] = 'none'
            
            # 格式化结果
            formatted_results = self.scoring_engine.format_recommendation_result(
                top_recommendations
            )
            
            self.logger.info(f"生成{len(formatted_results)}只推荐股票")
            
            # 5. 保存结果
            if save_results:
                self.logger.info("步骤5: 保存推荐结果")
                self.result_writer.write_buy_recommendations(formatted_results)
                
                if export_excel:
                    self.result_writer.export_to_excel(formatted_results)
                
                # 清理旧文件
                self.result_writer.cleanup_old_files()
            
            self.logger.info("股票推荐系统运行完成")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"股票推荐系统运行失败: {e}")
            raise
    
    def run_sell_analysis(self, 
                         portfolio_file: Optional[str] = None,
                         save_results: bool = True) -> List[Dict]:
        """
        运行卖出决策分析
        
        Args:
            portfolio_file: 持仓文件路径，如果为None则从历史推荐中加载
            save_results: 是否保存结果到文件
            
        Returns:
            卖出决策列表
        """
        try:
            self.logger.info("开始运行卖出决策分析...")
            
            # 加载持仓股票
            if portfolio_file:
                # 从指定文件加载
                import json
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
            else:
                # 从历史推荐中加载
                portfolio = self.result_writer.load_previous_recommendations()
            
            if not portfolio:
                self.logger.warning("没有找到持仓股票数据")
                return []
            
            # 提取股票代码
            stock_codes = [stock['stock_code'] for stock in portfolio]
            self.logger.info(f"分析{len(stock_codes)}只持仓股票")
            
            # 获取当前数据
            current_data = self.data_fetcher.get_all_data(stock_codes)
            
            # 提取特征
            current_features = self.feature_extractor.batch_extract_features(current_data)
            
            # 卖出决策分析
            sell_decisions = []
            
            for stock in portfolio:
                stock_code = stock['stock_code']
                
                if stock_code not in current_features:
                    continue
                
                features = current_features[stock_code]
                current_price = features.get('current_price', 0)
                original_price = stock.get('current_price', current_price)
                
                # 计算收益率
                return_rate = ((current_price - original_price) / original_price * 100 
                              if original_price > 0 else 0)
                
                # 重新评分
                total_score, score_details = self.scoring_engine.calculate_comprehensive_score(features)
                
                # 卖出决策逻辑
                sell_signal = False
                sell_reason = []
                
                # 止盈止损逻辑
                if return_rate >= 20:  # 止盈
                    sell_signal = True
                    sell_reason.append(f"达到止盈目标({return_rate:.1f}%)")
                elif return_rate <= -10:  # 止损
                    sell_signal = True
                    sell_reason.append(f"触发止损({return_rate:.1f}%)")
                
                # 技术面恶化
                if total_score < -5:
                    sell_signal = True
                    sell_reason.append("技术面恶化")
                
                # RSI过热
                if features.get('rsi', 50) > 80:
                    sell_signal = True
                    sell_reason.append("RSI过热")
                
                decision = {
                    'stock_code': stock_code,
                    'stock_name': features.get('stock_name', ''),
                    'original_price': original_price,
                    'current_price': current_price,
                    'return_rate': return_rate,
                    'current_score': total_score,
                    'sell_signal': sell_signal,
                    'sell_reason': '; '.join(sell_reason) if sell_reason else '持有',
                    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                sell_decisions.append(decision)
            
            # 保存卖出决策
            if save_results:
                self.result_writer.write_sell_decisions(sell_decisions)
            
            self.logger.info(f"卖出决策分析完成，共分析{len(sell_decisions)}只股票")
            return sell_decisions
            
        except Exception as e:
            self.logger.error(f"卖出决策分析失败: {e}")
            raise
    
    def get_performance_summary(self) -> Dict:
        """
        获取系统性能摘要
        
        Returns:
            性能摘要字典
        """
        try:
            return self.result_writer.get_performance_summary()
        except Exception as e:
            self.logger.error(f"获取性能摘要失败: {e}")
            return {}
    
    def print_results(self, results: List[Dict], result_type: str = "推荐"):
        """
        打印结果到控制台
        
        Args:
            results: 结果列表
            result_type: 结果类型（推荐/卖出）
        """
        print(f"\n=== {result_type}结果 ===")
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"共{len(results)}只股票\n")
        
        if result_type == "推荐":
            for result in results:
                print(f"排名{result['rank']:2d}: {result['stock_name']}({result['stock_code']})")
                print(f"         价格: {result['current_price']:6.2f} 涨跌: {result['change_pct']:+5.2f}%")
                print(f"         得分: {result['total_score']:6.2f}")
                print(f"         理由: {result['recommendation_reason']}")
                print()
        else:  # 卖出决策
            for result in results:
                signal = "🔴 卖出" if result['sell_signal'] else "🟢 持有"
                print(f"{signal}: {result['stock_name']}({result['stock_code']})")
                print(f"         收益: {result['return_rate']:+6.2f}% ({result['original_price']:.2f} -> {result['current_price']:.2f})")
                print(f"         得分: {result['current_score']:6.2f}")
                print(f"         建议: {result['sell_reason']}")
                print()

def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票推荐系统')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--stock-universe', default='default', 
                       choices=['default', 'conservative', 'aggressive'],
                       help='股票池策略')
    parser.add_argument('--factor-strategy', default='default',
                       choices=['default', 'momentum_focused', 'capital_flow_focused', 'conservative'],
                       help='因子策略')
    parser.add_argument('--time-period', default='default',
                       choices=['short_term', 'medium_term', 'long_term'],
                       help='时间周期')
    parser.add_argument('--top-n', type=int, default=10, help='推荐股票数量')
    parser.add_argument('--no-sell-analysis', action='store_true', help='跳过卖出分析')
    
    args = parser.parse_args()
    
    try:
        # 创建推荐系统实例
        system = StockRecommendationSystem(
            config_path=args.config,
            stock_universe=args.stock_universe,
            factor_strategy=args.factor_strategy,
            time_period=args.time_period
        )
        
        print(f"配置信息:")
        print(f"  股票池策略: {args.stock_universe}")
        print(f"  因子策略: {args.factor_strategy}")
        print(f"  时间周期: {args.time_period}")
        print(f"  推荐数量: {args.top_n}")
        print()
        
        # 运行推荐
        recommendations = system.run_recommendation(top_n=args.top_n)
        
        if recommendations:
            print(f"推荐成功！共推荐 {len(recommendations)} 只股票")
            
            # 运行卖出分析
            if not args.no_sell_analysis:
                sell_decisions = system.run_sell_analysis()
                if sell_decisions:
                    print(f"卖出分析完成！共分析 {len(sell_decisions)} 只股票")
        else:
            print("推荐失败")
            
    except Exception as e:
        print(f"系统运行出错：{e}")
        logger.error(f"系统运行出错：{e}")

if __name__ == "__main__":
    main()