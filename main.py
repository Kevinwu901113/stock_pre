#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股推荐系统主入口

该模块负责根据配置文件动态组合pipeline，
按需启用各模型模块（规则、ML、LLM、融合），
并提供统一的接口调用和日志输出。
"""

import os
import sys
import argparse
import datetime
from datetime import timedelta
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Tuple, Any

# 导入各模块
from utils.config_loader import load_config, get_config
from utils.logger import setup_logger, get_logger
from utils.date_utils import get_trade_dates, format_date

from data.fetch_data import StockDataFetcher
from data.preprocess import DataPreprocessor

from features.factor_engine import FactorEngine
from features.factor_selector import FactorSelector

from model.ml_model import MLModel, create_model
from model.predictor import BasePredictor, MLPredictor
from model.scorer import RuleScorer

from strategy.buy_strategy import TopNStrategy, ThresholdStrategy, SectorBalancedStrategy

from llm.news_collector import NewsCollector
from llm.llm_analyzer import LLMAnalyzer
from llm.llm_scoring import LLMScoring

from fusion.score_fusion import ScoreFusion

from strategy.buy_strategy import BuyStrategy

from backtest.simulator import BacktestSimulator
from backtest.evaluator import BacktestEvaluator


class StockRecommendationSystem:
    """A股推荐系统主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化推荐系统
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        # 加载配置
        load_config(config_path)
        
        # 设置日志
        log_config = get_config("logging")
        # 构建日志文件路径
        log_dir = log_config.get("log_dir", "./logs")
        today = datetime.datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'app_{today}.log')
        
        setup_logger(
            name="app",
            log_file=log_file,
            level=getattr(logging, log_config.get("level", "INFO").upper()),
            console_output=log_config.get("console_output", True),
            max_bytes=log_config.get("file_size_limit", 10) * 1024 * 1024,
            backup_count=log_config.get("backup_count", 5)
        )
        self.logger = get_logger("stock_recommendation")
        
        # 获取全局配置
        self.global_config = get_config("global")
        self.enabled_modules = self.global_config.get("enable_modules", {})
        self.top_n = self.global_config.get("top_n", 10)
        
        # 初始化组件
        self._init_data_components()
        
        # 根据配置动态初始化模型组件
        if self.enabled_modules.get("rule_model", False):
            self._init_rule_model()
        
        if self.enabled_modules.get("ml_model", False):
            self._init_ml_model()
        
        if self.enabled_modules.get("llm_model", False):
            self._init_llm_model()
        
        if self.enabled_modules.get("fusion", False):
            self._init_fusion_module()
        
        # 初始化策略和回测组件
        self._init_strategy_components()
        self._init_backtest_components()
        
        self.logger.info("A股推荐系统初始化完成")
    
    def _init_data_components(self):
        """初始化数据相关组件"""
        data_config = get_config("data_source")
        
        # 数据获取器
        self.data_fetcher = StockDataFetcher(
            data_source=data_config.get("type", "akshare"),
            local_data_path=data_config.get("cache_dir"),
            akshare_config=data_config.get("akshare", {})
        )
        
        # 数据预处理器
        self.preprocessor = DataPreprocessor()
        
        self.logger.info("数据组件初始化完成")
    
    def _init_rule_model(self):
        """初始化规则模型"""
        rule_config = get_config("rule_model")
        
        # 因子引擎
        self.factor_engine = FactorEngine()
        
        # 因子选择器
        self.factor_selector = FactorSelector()
        
        # 规则评分器
        self.rule_scorer = RuleScorer(
            factor_weights=rule_config.get("weights", {})
        )
        
        # 设置阈值（如果RuleScorer支持的话）
        thresholds = rule_config.get("thresholds", {})
        if hasattr(self.rule_scorer, 'set_thresholds') and thresholds:
            self.rule_scorer.set_thresholds(thresholds)
        
        # 创建规则预测器
        class RulePredictor(BasePredictor):
            def __init__(self, scorer):
                super().__init__(name="rule_predictor")
                self.scorer = scorer
            
            def predict(self, data):
                return self.scorer.score(data)
            
            def evaluate(self, data, target):
                predictions = self.predict(data)
                # 简单评估，实际应根据具体需求实现
                return {"accuracy": ((predictions > 0.5) == (target > 0)).mean()}
        
        self.rule_predictor = RulePredictor(self.rule_scorer)
        
        self.logger.info("规则模型初始化完成")
    
    def _init_ml_model(self):
        """初始化机器学习模型"""
        ml_config = get_config("model")
        
        # 创建ML模型
        self.ml_model = create_model(
            model_type=ml_config.get("type", "xgboost"),
            params=ml_config.get("params", {})
        )
        
        # 创建ML预测器
        self.ml_predictor = MLPredictor(model=self.ml_model, name="ml_predictor")
        
        # 设置目标变量
        self.ml_predictor.set_target_column(ml_config.get("target_variable", "next_day_return"))
        
        self.logger.info("机器学习模型初始化完成")
    
    def _init_llm_model(self):
        """初始化LLM模型"""
        llm_config = get_config("llm")
        api_key = llm_config.get("api_key")
        model_name = llm_config.get("model_name", "gpt-3.5-turbo")
        
        # 新闻收集器
        self.news_collector = NewsCollector()
        
        # LLM分析器
        self.llm_analyzer = LLMAnalyzer(api_key=api_key, model=model_name)
        
        # LLM评分器
        self.llm_scoring = LLMScoring()
        
        # 创建LLM预测器
        class LLMPredictor(BasePredictor):
            def __init__(self, analyzer, scoring):
                super().__init__(name="llm_predictor")
                self.analyzer = analyzer
                self.scoring = scoring
            
            def predict(self, news_data):
                # 分析新闻
                analysis_results = self.analyzer.analyze_news_batch(news_data)
                # 评分
                scores = self.scoring.score_analysis_results(analysis_results)
                return pd.Series(scores)
            
            def evaluate(self, news_data, target):
                predictions = self.predict(news_data)
                # 简单评估，实际应根据具体需求实现
                return {"correlation": predictions.corr(target)}
        
        self.llm_predictor = LLMPredictor(self.llm_analyzer, self.llm_scoring)
        
        self.logger.info("LLM模型初始化完成")
    
    def _init_fusion_module(self):
        """初始化融合模块"""
        fusion_config = get_config("score_fusion")
        
        # 创建评分融合器
        self.score_fusion = ScoreFusion(config=fusion_config)
        
        self.logger.info("融合模块初始化完成")
    
    def _init_strategy_components(self):
        """初始化策略组件"""
        strategy_config = get_config("strategy")
        
        # 买入策略 - 使用具体的策略实现
        strategy_type = strategy_config.get("type", "top_n")
        if strategy_type == "top_n":
            self.buy_strategy = TopNStrategy(
                top_n=strategy_config.get("max_positions", 10),
                score_column=strategy_config.get("score_column", "final_score")
            )
        elif strategy_type == "threshold":
            self.buy_strategy = ThresholdStrategy(
                threshold=strategy_config.get("threshold", 80.0),
                score_column=strategy_config.get("score_column", "final_score"),
                max_stocks=strategy_config.get("max_positions", 20)
            )
        elif strategy_type == "sector_balanced":
            self.buy_strategy = SectorBalancedStrategy(
                top_n=strategy_config.get("max_positions", 10),
                sector_limit=strategy_config.get("sector_limit", 2),
                score_column=strategy_config.get("score_column", "final_score"),
                sector_column=strategy_config.get("sector_column", "sector")
            )
        else:
            # 默认使用 TopNStrategy
            self.buy_strategy = TopNStrategy(
                top_n=strategy_config.get("max_positions", 10),
                score_column=strategy_config.get("score_column", "final_score")
            )
        
        # 添加风控规则
        risk_rules = strategy_config.get("risk_rules", {})
        if risk_rules.get("volatility_rule", {}).get("enabled", False):
            from strategy.buy_strategy import VolatilityRule
            volatility_config = risk_rules["volatility_rule"]
            self.buy_strategy.add_risk_rule(VolatilityRule(
                volatility_window=volatility_config.get("window", 20),
                max_volatility=volatility_config.get("max_volatility", 0.03)
            ))
        
        if risk_rules.get("turnover_rule", {}).get("enabled", False):
            from strategy.buy_strategy import TurnoverRule
            turnover_config = risk_rules["turnover_rule"]
            self.buy_strategy.add_risk_rule(TurnoverRule(
                min_turnover=turnover_config.get("min_turnover", 1.0),
                max_turnover=turnover_config.get("max_turnover", 15.0)
            ))
        
        if risk_rules.get("price_rule", {}).get("enabled", False):
            from strategy.buy_strategy import PriceRule
            price_config = risk_rules["price_rule"]
            self.buy_strategy.add_risk_rule(PriceRule(
                min_price=price_config.get("min_price", 5.0),
                max_price=price_config.get("max_price", 100.0)
            ))
        
        if risk_rules.get("st_rule", {}).get("enabled", True):  # 默认启用ST规则
            from strategy.buy_strategy import STRule
            self.buy_strategy.add_risk_rule(STRule())
        
        self.logger.info("策略组件初始化完成")
    
    def _init_backtest_components(self):
        """初始化回测组件"""
        backtest_config = get_config("backtest")
        
        # 回测模拟器
        self.backtest_simulator = BacktestSimulator(
            initial_capital=backtest_config.get("initial_capital", 1000000),
            commission_rate=backtest_config.get("commission_rate", 0.0003),
            slippage=backtest_config.get("slippage", 0.0002),
            max_position_per_stock=backtest_config.get("max_position_per_stock", 0.1),
            max_stocks_per_day=backtest_config.get("max_stocks_per_day", 5)
        )
        
        # 回测评估器
        self.backtest_evaluator = BacktestEvaluator(
            benchmark_data=None  # 可以后续通过 set_benchmark 方法设置
        )
        
        self.logger.info("回测组件初始化完成")
    
    def run_recommendation(self, date: str) -> pd.DataFrame:
        """运行推荐流程
        
        Args:
            date: 推荐日期，格式为YYYYMMDD
            
        Returns:
            推荐股票DataFrame
        """
        self.logger.info(f"开始运行推荐流程，日期: {date}")
        
        # 1. 获取数据
        self.logger.info("获取股票数据...")
        stock_list = self.data_fetcher.get_stock_list()
        
        # 如果配置了股票池，则过滤
        stock_pool = get_config("data_source").get("stock_pool", [])
        if stock_pool:
            stock_list = stock_list[stock_list['code'].isin(stock_pool)]
        
        # 获取历史数据（用于特征计算）
        start_date = (datetime.datetime.strptime(date, "%Y%m%d") - timedelta(days=180)).strftime("%Y%m%d")
        end_date = date
        
        # 存储每只股票的评分
        all_scores = {}
        
        # 2. 对每只股票进行评分
        for _, stock in stock_list.iterrows():
            stock_code = stock['code']
            try:
                # 获取股票数据
                stock_data = self.data_fetcher.get_stock_daily_data(stock_code, start_date, end_date)
                if stock_data.empty:
                    continue
                
                # 预处理数据
                processed_data = self.preprocessor.process(stock_data)
                
                # 计算特征
                if hasattr(self, 'factor_engine'):
                    features = self.factor_engine.calculate_all_factors(processed_data)
                else:
                    features = processed_data
                
                # 各模型评分
                scores = {}
                
                # 规则模型评分
                if hasattr(self, 'rule_predictor'):
                    rule_score = self.rule_predictor.predict(features).iloc[-1]
                    scores['rule_model'] = rule_score
                
                # ML模型评分
                if hasattr(self, 'ml_predictor'):
                    # 设置特征列
                    feature_cols = features.columns.tolist()
                    for col in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']:
                        if col in feature_cols:
                            feature_cols.remove(col)
                    
                    self.ml_predictor.set_feature_columns(feature_cols)
                    ml_score = self.ml_predictor.predict(features).iloc[-1]
                    scores['ml_model'] = ml_score
                
                # LLM模型评分
                if hasattr(self, 'llm_predictor') and hasattr(self, 'news_collector'):
                    # 获取相关新闻
                    news_date = (datetime.datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                    news_data = self.news_collector.collect_daily_news(news_date)
                    
                    if news_data:
                        llm_score = self.llm_predictor.predict(news_data).mean()
                        scores['llm_model'] = llm_score
                
                # 融合评分
                if hasattr(self, 'score_fusion') and scores:
                    final_score = self.score_fusion.fuse_scores(
                        ml_score=scores.get('ml_model'),
                        rule_score=scores.get('rule_model'),
                        llm_score=scores.get('llm_model')
                    )
                else:
                    # 如果没有融合模块，使用简单平均
                    final_score = sum(scores.values()) / len(scores) if scores else 0
                
                # 存储评分
                all_scores[stock_code] = {
                    'code': stock_code,
                    'name': stock['name'] if 'name' in stock else '',
                    'final_score': final_score,
                    **scores
                }
                
            except Exception as e:
                self.logger.error(f"处理股票 {stock_code} 时出错: {e}")
        
        # 3. 转换为DataFrame并排序
        if not all_scores:
            self.logger.warning("没有有效的评分数据")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(list(all_scores.values()))
        result_df = result_df.sort_values('final_score', ascending=False)
        
        # 4. 选择Top N
        top_n_stocks = result_df.head(self.top_n)
        
        self.logger.info(f"推荐流程完成，共推荐 {len(top_n_stocks)} 只股票")
        return top_n_stocks
    
    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """运行回测
        
        Args:
            start_date: 回测开始日期，格式为YYYYMMDD
            end_date: 回测结束日期，格式为YYYYMMDD
            
        Returns:
            回测结果字典
        """
        self.logger.info(f"开始回测，时间范围: {start_date} - {end_date}")
        
        # 获取交易日列表
        trade_dates = get_trade_dates(start_date, end_date)
        
        # 回测配置
        backtest_config = get_config("backtest")
        rebalance_freq = backtest_config.get("rebalance_frequency", "weekly")
        
        # 初始化回测
        self.backtest_simulator.initialize(
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=rebalance_freq
        )
        
        # 按照再平衡频率确定调仓日期
        rebalance_dates = []
        if rebalance_freq == "daily":
            rebalance_dates = trade_dates
        elif rebalance_freq == "weekly":
            # 每周一调仓
            for date in trade_dates:
                dt = datetime.datetime.strptime(date, "%Y%m%d")
                if dt.weekday() == 0:  # 周一
                    rebalance_dates.append(date)
        elif rebalance_freq == "monthly":
            # 每月第一个交易日调仓
            current_month = None
            for date in trade_dates:
                dt = datetime.datetime.strptime(date, "%Y%m%d")
                if dt.month != current_month:
                    current_month = dt.month
                    rebalance_dates.append(date)
        
        # 运行回测
        for date in trade_dates:
            # 获取市场数据
            market_data = self.data_fetcher.get_market_index_data(
                backtest_config.get("benchmark", "sh000001"),
                date, date
            )
            
            # 更新市场数据
            self.backtest_simulator.update_market_data(date, market_data)
            
            # 如果是调仓日，生成推荐并调仓
            if date in rebalance_dates:
                try:
                    # 获取推荐股票
                    recommendations = self.run_recommendation(date)
                    
                    if not recommendations.empty:
                        # 生成调仓决策
                        positions = self.buy_strategy.generate_positions(recommendations)
                        
                        # 执行调仓
                        self.backtest_simulator.rebalance(date, positions)
                except Exception as e:
                    self.logger.error(f"调仓日 {date} 处理失败: {e}")
            
            # 更新持仓
            self.backtest_simulator.update_portfolio(date)
        
        # 获取回测结果
        backtest_results = self.backtest_simulator.get_results()
        
        # 评估回测结果
        evaluation = self.backtest_evaluator.evaluate(backtest_results)
        
        # 合并结果
        results = {
            "portfolio_value": backtest_results["portfolio_value"],
            "returns": backtest_results["returns"],
            "positions": backtest_results["positions"],
            "trades": backtest_results["trades"],
            "evaluation": evaluation
        }
        
        self.logger.info("回测完成")
        return results
    
    def output_results(self, results: Union[pd.DataFrame, Dict[str, Any]], mode: str):
        """输出结果
        
        Args:
            results: 推荐结果或回测结果
            mode: 模式，'recommend'或'backtest'
        """
        output_config = get_config("output")
        report_dir = output_config.get("report_dir", "./reports")
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if mode == "recommend":
            # 输出推荐结果
            if isinstance(results, pd.DataFrame) and not results.empty:
                # 保存为CSV
                if output_config.get("export_csv", True):
                    csv_path = os.path.join(report_dir, f"recommendations_{timestamp}.csv")
                    results.to_csv(csv_path, index=False, encoding='utf-8')
                    self.logger.info(f"推荐结果已保存至: {csv_path}")
                
                # 生成HTML报告
                if output_config.get("generate_html", True):
                    html_path = os.path.join(report_dir, f"recommendations_{timestamp}.html")
                    html_content = f"""
                    <html>
                    <head>
                        <title>A股推荐系统 - 推荐结果</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        </style>
                    </head>
                    <body>
                        <h1>A股推荐系统 - 推荐结果</h1>
                        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        {results.to_html(index=False)}
                    </body>
                    </html>
                    """
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.logger.info(f"HTML报告已保存至: {html_path}")
            else:
                self.logger.warning("没有可输出的推荐结果")
        
        elif mode == "backtest":
            # 输出回测结果
            if results:
                # 保存为CSV
                if output_config.get("export_csv", True):
                    # 保存回测评估指标
                    eval_df = pd.DataFrame([results["evaluation"]])
                    eval_path = os.path.join(report_dir, f"backtest_evaluation_{timestamp}.csv")
                    eval_df.to_csv(eval_path, index=False, encoding='utf-8')
                    
                    # 保存回测收益曲线
                    returns_df = pd.DataFrame({
                        "date": list(results["portfolio_value"].keys()),
                        "portfolio_value": list(results["portfolio_value"].values())
                    })
                    returns_path = os.path.join(report_dir, f"backtest_returns_{timestamp}.csv")
                    returns_df.to_csv(returns_path, index=False, encoding='utf-8')
                    
                    self.logger.info(f"回测结果已保存至: {eval_path} 和 {returns_path}")
                
                # 生成图表
                if output_config.get("plot_results", True):
                    try:
                        import matplotlib.pyplot as plt
                        import seaborn as sns
                        
                        # 设置样式
                        sns.set_style("whitegrid")
                        plt.figure(figsize=(12, 6))
                        
                        # 绘制收益曲线
                        dates = [datetime.datetime.strptime(d, "%Y%m%d") for d in results["portfolio_value"].keys()]
                        values = list(results["portfolio_value"].values())
                        plt.plot(dates, values, label="Portfolio Value")
                        
                        # 添加标题和标签
                        plt.title("Backtest Results", fontsize=16)
                        plt.xlabel("Date")
                        plt.ylabel("Portfolio Value")
                        plt.legend()
                        plt.grid(True)
                        
                        # 保存图表
                        chart_path = os.path.join(report_dir, f"backtest_chart_{timestamp}.png")
                        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
                        plt.close()
                        
                        self.logger.info(f"回测图表已保存至: {chart_path}")
                    except Exception as e:
                        self.logger.error(f"生成回测图表失败: {e}")
                
                # 生成HTML报告
                if output_config.get("generate_html", True):
                    # 构建评估指标表格
                    eval_html = pd.DataFrame([results["evaluation"]]).to_html(index=False)
                    
                    # 构建收益曲线表格
                    returns_df = pd.DataFrame({
                        "date": list(results["portfolio_value"].keys()),
                        "portfolio_value": list(results["portfolio_value"].values())
                    })
                    returns_html = returns_df.to_html(index=False)
                    
                    html_path = os.path.join(report_dir, f"backtest_report_{timestamp}.html")
                    html_content = f"""
                    <html>
                    <head>
                        <title>A股推荐系统 - 回测报告</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                            h2 {{ color: #333; margin-top: 30px; }}
                        </style>
                    </head>
                    <body>
                        <h1>A股推荐系统 - 回测报告</h1>
                        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        
                        <h2>回测评估指标</h2>
                        {eval_html}
                        
                        <h2>收益曲线</h2>
                        {returns_html}
                    </body>
                    </html>
                    """
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.logger.info(f"HTML报告已保存至: {html_path}")
            else:
                self.logger.warning("没有可输出的回测结果")
        
        else:
            self.logger.error(f"未知的输出模式: {mode}")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="A股推荐系统")
    parser.add_argument("--mode", choices=["recommend", "backtest"], default="recommend",
                        help="运行模式: recommend (推荐) 或 backtest (回测)")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--date", type=str, help="推荐日期 (YYYYMMDD格式)")
    parser.add_argument("--start_date", type=str, help="回测开始日期 (YYYYMMDD格式)")
    parser.add_argument("--end_date", type=str, help="回测结束日期 (YYYYMMDD格式)")
    
    args = parser.parse_args()
    
    # 初始化系统
    system = StockRecommendationSystem(config_path=args.config)
    
    # 根据模式运行
    if args.mode == "recommend":
        # 如果未指定日期，使用当前日期
        date = args.date or datetime.datetime.now().strftime("%Y%m%d")
        
        # 运行推荐
        recommendations = system.run_recommendation(date)
        
        # 输出结果
        system.output_results(recommendations, "recommend")
        
        # 打印推荐结果
        if not recommendations.empty:
            print(f"\n推荐股票 (日期: {date}):\n")
            print(recommendations[["code", "name", "final_score"]].to_string(index=False))
        else:
            print("\n没有推荐结果\n")
    
    elif args.mode == "backtest":
        # 如果未指定日期，使用默认日期范围
        start_date = args.start_date or "20230101"
        end_date = args.end_date or datetime.now().strftime("%Y%m%d")
        
        # 运行回测
        backtest_results = system.run_backtest(start_date, end_date)
        
        # 输出结果
        system.output_results(backtest_results, "backtest")
        
        # 打印回测结果
        if backtest_results:
            print(f"\n回测结果 (时间范围: {start_date} - {end_date}):\n")
            for key, value in backtest_results["evaluation"].items():
                print(f"{key}: {value:.4f}")
        else:
            print("\n没有回测结果\n")


if __name__ == "__main__":
    main()