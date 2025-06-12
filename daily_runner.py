#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票推荐系统每日自动调度脚本
功能：自动执行推荐流程，包括读取配置、检查缓存、构造因子、调用预测模型、融合打分、输出结果、生成日志
"""

import os
import sys
import argparse
import logging
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入所需模块
from main import StockRecommendationSystem
from recommendation_fusion import RecommendationFusion
from enhanced_fusion_strategy import EnhancedFusionStrategy
from cache_manager import CacheManager


class DailyRunner:
    """股票推荐系统每日调度器"""
    
    def __init__(self, config_path: str = "config.yaml", 
                 fusion_config_path: str = "fusion_config.yaml",
                 run_date: Optional[str] = None):
        """
        初始化每日调度器
        
        Args:
            config_path: 主配置文件路径
            fusion_config_path: 融合策略配置文件路径
            run_date: 运行日期，格式YYYYMMDD，默认为当天
        """
        self.config_path = config_path
        self.fusion_config_path = fusion_config_path
        
        # 设置运行日期
        if run_date:
            try:
                self.run_date = datetime.strptime(run_date, "%Y%m%d")
            except ValueError:
                print(f"错误：日期格式不正确，应为YYYYMMDD，例如20230101，收到的是{run_date}")
                sys.exit(1)
        else:
            self.run_date = datetime.now()
            
        self.date_str = self.run_date.strftime("%Y%m%d")
        
        # 加载配置
        self.config = self._load_config(config_path)
        self.fusion_config = self._load_config(fusion_config_path)
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 创建结果和日志目录
        self.result_dir = Path(self.fusion_config.get("output", {}).get("output_dir", "result"))
        self.logs_dir = Path("logs")
        self._ensure_directories()
        
        self.logger.info(f"股票推荐系统每日调度器初始化完成，运行日期：{self.date_str}")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件 {config_path} 失败: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """设置日志配置"""
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        # 设置日志格式和输出
        log_file = f"logs/{self.date_str}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"结果目录: {self.result_dir}")
        self.logger.info(f"日志目录: {self.logs_dir}")
    
    def check_data_cache(self) -> bool:
        """检查数据缓存状态"""
        self.logger.info("检查数据缓存...")
        
        # 获取缓存配置
        cache_dir = self.config.get("data_source", {}).get("cache_dir", "data_cache")
        cache_expire_days = self.config.get("data_source", {}).get("cache_expire_days", 7)
        
        # 检查缓存目录是否存在
        if not os.path.exists(cache_dir):
            self.logger.warning(f"缓存目录 {cache_dir} 不存在，将创建")
            os.makedirs(cache_dir, exist_ok=True)
            return False
        
        # 检查缓存是否过期
        cache_manager = CacheManager(cache_dir)
        
        # 这里可以添加更详细的缓存检查逻辑
        # 例如检查特定的缓存文件是否存在和是否过期
        
        self.logger.info("数据缓存检查完成")
        return True
    
    def run_recommendation(self, stock_universe: str = "default", 
                          factor_strategy: str = "default",
                          time_period: str = "default",
                          top_n: int = 20) -> List[Dict]:
        """运行股票推荐流程
        
        Args:
            stock_universe: 股票池策略
            factor_strategy: 因子策略
            time_period: 时间周期
            top_n: 推荐数量
            
        Returns:
            推荐结果列表
        """
        self.logger.info(f"开始运行股票推荐流程 - 股票池: {stock_universe}, 因子策略: {factor_strategy}, 时间周期: {time_period}")
        
        try:
            # 创建推荐系统实例
            system = StockRecommendationSystem(
                config_path=self.config_path,
                stock_universe=stock_universe,
                factor_strategy=factor_strategy,
                time_period=time_period
            )
            
            # 运行推荐
            recommendations = system.run_recommendation(
                top_n=top_n,
                save_results=False  # 不保存结果，由本脚本统一管理
            )
            
            self.logger.info(f"推荐流程完成，获取到 {len(recommendations)} 只推荐股票")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"推荐流程运行失败: {e}", exc_info=True)
            return []
    
    def run_fusion_strategy(self, recommendations: List[Dict], 
                           method: str = "consensus_boost",
                           top_n: int = 10) -> List[Dict]:
        """运行融合策略
        
        Args:
            recommendations: 基础推荐结果
            method: 融合方法
            top_n: 推荐数量
            
        Returns:
            融合后的推荐结果
        """
        self.logger.info(f"开始运行融合策略 - 方法: {method}, 推荐数量: {top_n}")
        
        try:
            # 创建融合策略实例
            fusion = EnhancedFusionStrategy(self.fusion_config_path)
            
            # 运行融合策略
            fusion_results = fusion.run_fusion(
                recommendations,
                method=method,
                top_n=top_n
            )
            
            self.logger.info(f"融合策略完成，获取到 {len(fusion_results)} 只推荐股票")
            return fusion_results
            
        except Exception as e:
            self.logger.error(f"融合策略运行失败: {e}", exc_info=True)
            return recommendations[:top_n] if len(recommendations) >= top_n else recommendations
    
    def save_results(self, recommendations: List[Dict]) -> str:
        """保存推荐结果
        
        Args:
            recommendations: 推荐结果列表
            
        Returns:
            保存的文件路径
        """
        self.logger.info("保存推荐结果...")
        
        # 构建结果文件路径
        result_file = self.result_dir / f"{self.date_str}_buy.json"
        
        try:
            # 添加时间戳
            result_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "date": self.date_str,
                "count": len(recommendations),
                "recommendations": recommendations
            }
            
            # 写入JSON文件
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"推荐结果已保存到: {result_file}")
            return str(result_file)
            
        except Exception as e:
            self.logger.error(f"保存推荐结果失败: {e}", exc_info=True)
            return ""
    
    def run(self, stock_universe: str = "default", 
            factor_strategy: str = "default",
            time_period: str = "default",
            fusion_method: str = "consensus_boost",
            top_n: int = 10,
            save_intermediate_results: bool = False) -> Dict:
        """运行完整的每日推荐流程
        
        Args:
            stock_universe: 股票池策略
            factor_strategy: 因子策略
            time_period: 时间周期
            fusion_method: 融合方法
            top_n: 推荐数量
            save_intermediate_results: 是否保存中间结果
            
        Returns:
            运行结果摘要
        """
        start_time = datetime.now()
        self.logger.info(f"开始运行每日推荐流程 - 日期: {self.date_str}")
        
        try:
            # 1. 检查数据缓存
            self.check_data_cache()
            
            # 2. 运行基础推荐
            recommendations = self.run_recommendation(
                stock_universe=stock_universe,
                factor_strategy=factor_strategy,
                time_period=time_period,
                top_n=top_n * 2  # 获取更多候选，用于融合
            )
            
            # 保存中间结果（如果需要）
            if save_intermediate_results and recommendations:
                intermediate_file = self.result_dir / f"{self.date_str}_intermediate.json"
                with open(intermediate_file, 'w', encoding='utf-8') as f:
                    json.dump(recommendations, f, ensure_ascii=False, indent=2)
                self.logger.info(f"中间结果已保存到: {intermediate_file}")
            
            # 3. 运行融合策略
            if recommendations:
                final_recommendations = self.run_fusion_strategy(
                    recommendations=recommendations,
                    method=fusion_method,
                    top_n=top_n
                )
            else:
                self.logger.warning("基础推荐为空，跳过融合策略")
                final_recommendations = []
            
            # 4. 保存最终结果
            result_file = ""
            if final_recommendations:
                result_file = self.save_results(final_recommendations)
            else:
                self.logger.warning("没有推荐结果可保存")
            
            # 5. 生成运行摘要
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = {
                "date": self.date_str,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration,
                "stock_universe": stock_universe,
                "factor_strategy": factor_strategy,
                "time_period": time_period,
                "fusion_method": fusion_method,
                "recommendation_count": len(final_recommendations),
                "result_file": result_file,
                "status": "success"
            }
            
            self.logger.info(f"每日推荐流程完成 - 耗时: {duration:.2f}秒, 推荐数量: {len(final_recommendations)}")
            return summary
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(f"每日推荐流程失败: {e}", exc_info=True)
            
            # 生成失败摘要
            summary = {
                "date": self.date_str,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration,
                "status": "failed",
                "error": str(e)
            }
            
            return summary


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票推荐系统每日调度器')
    parser.add_argument('--config', default='config.yaml', help='主配置文件路径')
    parser.add_argument('--fusion-config', default='fusion_config.yaml', help='融合策略配置文件路径')
    parser.add_argument('--date', help='运行日期，格式YYYYMMDD，默认为当天')
    parser.add_argument('--stock-universe', default='default', 
                       choices=['default', 'conservative', 'aggressive'],
                       help='股票池策略')
    parser.add_argument('--factor-strategy', default='default',
                       choices=['default', 'momentum_focused', 'capital_flow_focused', 'conservative'],
                       help='因子策略')
    parser.add_argument('--time-period', default='default',
                       choices=['short_term', 'medium_term', 'long_term'],
                       help='时间周期')
    parser.add_argument('--fusion-method', default='consensus_boost',
                       choices=['weighted_average', 'filter_first', 'rank_adjustment', 'consensus_boost'],
                       help='融合方法')
    parser.add_argument('--top-n', type=int, default=10, help='推荐股票数量')
    parser.add_argument('--save-intermediate', action='store_true', help='保存中间结果')
    
    args = parser.parse_args()
    
    # 创建并运行每日调度器
    runner = DailyRunner(
        config_path=args.config,
        fusion_config_path=args.fusion_config,
        run_date=args.date
    )
    
    # 运行推荐流程
    summary = runner.run(
        stock_universe=args.stock_universe,
        factor_strategy=args.factor_strategy,
        time_period=args.time_period,
        fusion_method=args.fusion_method,
        top_n=args.top_n,
        save_intermediate_results=args.save_intermediate
    )
    
    # 打印运行摘要
    if summary["status"] == "success":
        print(f"\n推荐流程成功完成!")
        print(f"日期: {summary['date']}")
        print(f"推荐数量: {summary['recommendation_count']}")
        print(f"结果文件: {summary['result_file']}")
        print(f"耗时: {summary['duration_seconds']:.2f}秒")
    else:
        print(f"\n推荐流程失败!")
        print(f"错误: {summary['error']}")
        print(f"耗时: {summary['duration_seconds']:.2f}秒")
        sys.exit(1)


if __name__ == "__main__":
    main()