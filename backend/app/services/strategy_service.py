#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略服务模块
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from fastapi import Depends
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..core.config import settings
from ..core.logging import get_logger
from ..models.strategy import (
    StrategyInfo, StrategyConfig, StrategySignal,
    StrategyPerformance, StrategyComparison, ScheduleStatus
)
from .data_service import DataService

logger = get_logger(__name__)


class StrategyService:
    """策略服务类"""
    
    def __init__(self, data_service: DataService = Depends(DataService)):
        """初始化策略服务"""
        self.data_service = data_service
        self.strategies = {}
        self.scheduler = AsyncIOScheduler()
        self.schedule_status = {
            "is_running": False,
            "last_run": None,
            "next_run": None
        }
        
        # 初始化策略
        self._initialize_strategies()
        
        logger.info("策略服务初始化完成")
    
    def _initialize_strategies(self):
        """初始化策略配置"""
        # 尾盘买入策略
        self.strategies["evening_buy"] = {
            "name": "尾盘5分钟均线突破买入",
            "description": "基于5分钟均线突破的尾盘买入策略",
            "type": "buy",
            "timeframe": "5min",
            "direction": "long",
            "status": "active",
            "parameters": {
                "ma_period": 5,
                "volume_threshold": 1.5,
                "price_change_min": 0,
                "price_change_max": 5,
                "min_price": 5,
                "max_price": 100,
                "confidence_threshold": 60
            },
            "risk_management": {
                "stop_loss_pct": 3.0,
                "take_profit_pct": 5.0,
                "max_position_size": 10000
            },
            "schedule": {
                "enabled": True,
                "cron": "0 14 * * 1-5",  # 每个交易日14:00执行
                "description": "交易日下午2点执行"
            }
        }
        
        # 早盘卖出策略
        self.strategies["morning_sell"] = {
            "name": "早盘高开高走止盈",
            "description": "基于高开高走形态的早盘卖出策略",
            "type": "sell",
            "timeframe": "1min",
            "direction": "short",
            "status": "active",
            "parameters": {
                "min_gap_up": 1.0,
                "min_intraday_gain": 3.0,
                "cumulative_return_threshold": 10.0,
                "volume_amplification": 2.0,
                "confidence_threshold": 70
            },
            "risk_management": {
                "take_profit_pct": 3.0,
                "max_holding_period": 30  # 分钟
            },
            "schedule": {
                "enabled": True,
                "cron": "30 9 * * 1-5",  # 每个交易日9:30执行
                "description": "交易日上午9点30分执行"
            }
        }
        
        logger.info(f"初始化了 {len(self.strategies)} 个策略")
    
    async def get_strategy_list(self) -> List[Dict[str, Any]]:
        """获取所有可用策略列表"""
        try:
            strategy_list = []
            
            for strategy_name, strategy_config in self.strategies.items():
                strategy_info = {
                    "strategy_name": strategy_name,
                    "display_name": strategy_config["name"],
                    "description": strategy_config["description"],
                    "type": strategy_config["type"],
                    "timeframe": strategy_config["timeframe"],
                    "direction": strategy_config["direction"],
                    "status": strategy_config["status"],
                    "schedule_enabled": strategy_config["schedule"]["enabled"]
                }
                strategy_list.append(strategy_info)
            
            logger.info(f"返回 {len(strategy_list)} 个策略")
            return strategy_list
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {str(e)}")
            raise
    
    async def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取指定策略的详细信息"""
        try:
            if strategy_name not in self.strategies:
                logger.warning(f"策略不存在: {strategy_name}")
                return None
            
            strategy_config = self.strategies[strategy_name]
            
            strategy_info = {
                "strategy_name": strategy_name,
                "display_name": strategy_config["name"],
                "description": strategy_config["description"],
                "type": strategy_config["type"],
                "timeframe": strategy_config["timeframe"],
                "direction": strategy_config["direction"],
                "status": strategy_config["status"],
                "parameters": strategy_config["parameters"],
                "risk_management": strategy_config["risk_management"],
                "schedule": strategy_config["schedule"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            return strategy_info
            
        except Exception as e:
            logger.error(f"获取策略信息失败: {str(e)}")
            raise
    
    async def get_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略配置"""
        try:
            if strategy_name not in self.strategies:
                logger.warning(f"策略不存在: {strategy_name}")
                return None
            
            strategy_config = self.strategies[strategy_name]
            
            config = {
                "parameters": strategy_config["parameters"],
                "risk_management": strategy_config["risk_management"],
                "schedule": strategy_config["schedule"]
            }
            
            return config
            
        except Exception as e:
            logger.error(f"获取策略配置失败: {str(e)}")
            raise
    
    async def update_strategy_config(
        self,
        strategy_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新策略配置"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_name}")
            
            # 更新配置
            if "parameters" in config:
                self.strategies[strategy_name]["parameters"].update(config["parameters"])
            
            if "risk_management" in config:
                self.strategies[strategy_name]["risk_management"].update(config["risk_management"])
            
            if "schedule" in config:
                self.strategies[strategy_name]["schedule"].update(config["schedule"])
            
            logger.info(f"策略配置已更新: {strategy_name}")
            
            return await self.get_strategy_config(strategy_name)
            
        except Exception as e:
            logger.error(f"更新策略配置失败: {str(e)}")
            raise
    
    async def run_strategy(
        self,
        strategy_name: str,
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行指定策略"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_name}")
            
            logger.info(f"运行策略: {strategy_name}")
            
            strategy_config = self.strategies[strategy_name]
            
            # 设置默认参数
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # 获取股票池
            if not stock_codes:
                stock_codes = await self._get_default_stock_pool()
            
            # 运行策略
            if strategy_name == "evening_buy":
                signals = await self._run_evening_buy_strategy(stock_codes, start_date, end_date)
            elif strategy_name == "morning_sell":
                signals = await self._run_morning_sell_strategy(stock_codes, start_date, end_date)
            else:
                raise ValueError(f"不支持的策略: {strategy_name}")
            
            result = {
                "strategy_name": strategy_name,
                "run_time": datetime.now().isoformat(),
                "stock_count": len(stock_codes),
                "signal_count": len(signals),
                "signals": signals,
                "parameters": strategy_config["parameters"]
            }
            
            logger.info(f"策略运行完成: {strategy_name}, 生成 {len(signals)} 个信号")
            return result
            
        except Exception as e:
            logger.error(f"运行策略失败: {str(e)}")
            raise
    
    async def _run_evening_buy_strategy(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """运行尾盘买入策略"""
        signals = []
        strategy_config = self.strategies["evening_buy"]
        params = strategy_config["parameters"]
        
        for stock_code in stock_codes:
            try:
                # 获取股票数据
                stock_data = await self.data_service.get_stock_data(stock_code, start_date, end_date)
                if stock_data.empty:
                    continue
                
                # 应用策略逻辑
                latest = stock_data.iloc[-1]
                recent_data = stock_data.tail(params["ma_period"])
                
                # 计算均线
                ma = recent_data['close_price'].mean()
                
                # 计算成交量比率
                avg_volume = recent_data['volume'].mean()
                volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
                
                # 检查条件
                conditions = {
                    "price_above_ma": latest['close_price'] > ma,
                    "volume_sufficient": volume_ratio >= params["volume_threshold"],
                    "price_change_ok": params["price_change_min"] <= latest.get('pct_change', 0) <= params["price_change_max"],
                    "price_range_ok": params["min_price"] <= latest['close_price'] <= params["max_price"]
                }
                
                # 计算置信度
                confidence = sum(conditions.values()) * 25  # 每个条件25分
                
                if confidence >= params["confidence_threshold"]:
                    signal = {
                        "stock_code": stock_code,
                        "signal_type": "buy",
                        "signal_time": latest['trade_date'],
                        "price": float(latest['close_price']),
                        "confidence": confidence,
                        "conditions": conditions,
                        "indicators": {
                            "ma": ma,
                            "volume_ratio": volume_ratio,
                            "pct_change": latest.get('pct_change', 0)
                        }
                    }
                    signals.append(signal)
                    
            except Exception as e:
                logger.warning(f"处理股票 {stock_code} 时出错: {str(e)}")
                continue
        
        return signals
    
    async def _run_morning_sell_strategy(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """运行早盘卖出策略"""
        signals = []
        strategy_config = self.strategies["morning_sell"]
        params = strategy_config["parameters"]
        
        for stock_code in stock_codes:
            try:
                # 获取股票数据
                stock_data = await self.data_service.get_stock_data(stock_code, start_date, end_date)
                if stock_data.empty:
                    continue
                
                # 应用策略逻辑
                latest = stock_data.iloc[-1]
                previous = stock_data.iloc[-2] if len(stock_data) > 1 else latest
                
                # 计算指标
                gap_up = (latest['open_price'] - previous['close_price']) / previous['close_price'] * 100
                intraday_gain = (latest['close_price'] - latest['open_price']) / latest['open_price'] * 100
                
                # 检查条件
                conditions = {
                    "gap_up_sufficient": gap_up >= params["min_gap_up"],
                    "intraday_gain_ok": intraday_gain >= params["min_intraday_gain"],
                    "high_open_high_go": latest['close_price'] > latest['open_price'] > previous['close_price']
                }
                
                # 计算置信度
                confidence = sum(conditions.values()) * 30  # 每个条件30分
                
                if confidence >= params["confidence_threshold"]:
                    signal = {
                        "stock_code": stock_code,
                        "signal_type": "sell",
                        "signal_time": latest['trade_date'],
                        "price": float(latest['close_price']),
                        "confidence": confidence,
                        "conditions": conditions,
                        "indicators": {
                            "gap_up": gap_up,
                            "intraday_gain": intraday_gain
                        }
                    }
                    signals.append(signal)
                    
            except Exception as e:
                logger.warning(f"处理股票 {stock_code} 时出错: {str(e)}")
                continue
        
        return signals
    
    async def backtest_strategy(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        """策略回测"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_name}")
            
            logger.info(f"开始回测策略: {strategy_name}")
            
            # TODO: 实现完整的回测逻辑
            # 这里返回模拟的回测结果
            backtest_result = {
                "strategy_name": strategy_name,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_capital": initial_capital * 1.15,  # 模拟15%收益
                "total_return": 15.0,
                "annual_return": 18.5,
                "max_drawdown": -8.2,
                "sharpe_ratio": 1.35,
                "win_rate": 65.0,
                "total_trades": 45,
                "winning_trades": 29,
                "losing_trades": 16,
                "avg_win": 4.2,
                "avg_loss": -2.8,
                "profit_factor": 1.85,
                "trades": []  # 详细交易记录
            }
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"策略回测失败: {str(e)}")
            raise
    
    async def get_strategy_performance(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """获取策略表现统计"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_name}")
            
            logger.info(f"获取策略表现: {strategy_name}")
            
            # TODO: 实现实际的表现统计逻辑
            # 这里返回模拟数据
            performance = {
                "strategy_name": strategy_name,
                "period": f"{start_date} 到 {end_date}",
                "total_signals": 85,
                "successful_signals": 55,
                "success_rate": 64.7,
                "average_return": 3.8,
                "total_return": 12.5,
                "max_return": 18.5,
                "min_return": -6.2,
                "volatility": 15.2,
                "sharpe_ratio": 1.25,
                "max_drawdown": -8.5,
                "win_rate": 67.0,
                "profit_factor": 1.75
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"获取策略表现失败: {str(e)}")
            raise
    
    async def compare_strategies(
        self,
        strategy_names: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """策略对比分析"""
        try:
            logger.info(f"对比策略: {strategy_names}")
            
            comparison_result = {
                "comparison_period": f"{start_date} 到 {end_date}",
                "strategies": [],
                "summary": {
                    "best_return": None,
                    "best_sharpe": None,
                    "lowest_drawdown": None,
                    "highest_win_rate": None
                }
            }
            
            # 获取每个策略的表现
            for strategy_name in strategy_names:
                if strategy_name in self.strategies:
                    performance = await self.get_strategy_performance(strategy_name, start_date, end_date)
                    comparison_result["strategies"].append(performance)
            
            # 计算最佳表现
            if comparison_result["strategies"]:
                strategies = comparison_result["strategies"]
                comparison_result["summary"] = {
                    "best_return": max(strategies, key=lambda x: x["total_return"])["strategy_name"],
                    "best_sharpe": max(strategies, key=lambda x: x["sharpe_ratio"])["strategy_name"],
                    "lowest_drawdown": min(strategies, key=lambda x: abs(x["max_drawdown"]))["strategy_name"],
                    "highest_win_rate": max(strategies, key=lambda x: x["win_rate"])["strategy_name"]
                }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"策略对比失败: {str(e)}")
            raise
    
    async def get_schedule_status(self) -> Dict[str, Any]:
        """获取策略调度状态"""
        try:
            status = {
                "scheduler_running": self.scheduler.running,
                "scheduled_jobs": [],
                "last_run": self.schedule_status["last_run"],
                "next_run": self.schedule_status["next_run"]
            }
            
            # 获取调度任务信息
            for job in self.scheduler.get_jobs():
                job_info = {
                    "job_id": job.id,
                    "strategy_name": job.id.replace("_job", ""),
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                status["scheduled_jobs"].append(job_info)
            
            return status
            
        except Exception as e:
            logger.error(f"获取调度状态失败: {str(e)}")
            raise
    
    async def start_schedule(self) -> Dict[str, Any]:
        """启动策略调度"""
        try:
            logger.info("启动策略调度")
            
            if not self.scheduler.running:
                # 添加调度任务
                for strategy_name, strategy_config in self.strategies.items():
                    if strategy_config["schedule"]["enabled"]:
                        cron_expr = strategy_config["schedule"]["cron"]
                        
                        # 解析cron表达式
                        cron_parts = cron_expr.split()
                        trigger = CronTrigger(
                            minute=cron_parts[0],
                            hour=cron_parts[1],
                            day=cron_parts[2],
                            month=cron_parts[3],
                            day_of_week=cron_parts[4]
                        )
                        
                        self.scheduler.add_job(
                            self._scheduled_strategy_run,
                            trigger=trigger,
                            id=f"{strategy_name}_job",
                            args=[strategy_name],
                            replace_existing=True
                        )
                        
                        logger.info(f"添加调度任务: {strategy_name} - {cron_expr}")
                
                # 启动调度器
                self.scheduler.start()
                self.schedule_status["is_running"] = True
                
                logger.info("策略调度已启动")
            
            return await self.get_schedule_status()
            
        except Exception as e:
            logger.error(f"启动策略调度失败: {str(e)}")
            raise
    
    async def stop_schedule(self) -> Dict[str, Any]:
        """停止策略调度"""
        try:
            logger.info("停止策略调度")
            
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.schedule_status["is_running"] = False
                
                logger.info("策略调度已停止")
            
            return await self.get_schedule_status()
            
        except Exception as e:
            logger.error(f"停止策略调度失败: {str(e)}")
            raise
    
    async def _scheduled_strategy_run(self, strategy_name: str):
        """调度执行策略"""
        try:
            logger.info(f"调度执行策略: {strategy_name}")
            
            # 运行策略
            result = await self.run_strategy(strategy_name)
            
            # 更新调度状态
            self.schedule_status["last_run"] = datetime.now().isoformat()
            
            logger.info(f"调度策略执行完成: {strategy_name}, 生成 {result['signal_count']} 个信号")
            
        except Exception as e:
            logger.error(f"调度策略执行失败: {strategy_name} - {str(e)}")
    
    async def _get_default_stock_pool(self) -> List[str]:
        """获取默认股票池"""
        # 返回一些模拟的股票代码
        return [
            "600000", "600001", "600002", "600003", "600004",
            "600005", "600006", "600007", "600008", "600009",
            "000001", "000002", "000003", "000004", "000005",
            "300001", "300002", "300003", "300004", "300005"
        ]