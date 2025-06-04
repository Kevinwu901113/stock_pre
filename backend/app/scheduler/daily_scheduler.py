#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日调度脚本
支持策略的定时执行、模拟运行和任务管理
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, time, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from ..core.config import settings
from ..core.logging import get_logger
from ..services.data_service import DataService
from ..services.strategy_service import StrategyService
from ..strategies.strategy_combiner import StrategyCombiner

logger = get_logger(__name__)


class TaskType(str, Enum):
    """任务类型"""
    STRATEGY_RUN = "strategy_run"           # 策略运行
    DATA_UPDATE = "data_update"             # 数据更新
    BACKTEST = "backtest"                   # 回测
    REPORT_GENERATE = "report_generate"     # 报告生成
    CLEANUP = "cleanup"                     # 清理任务
    HEALTH_CHECK = "health_check"           # 健康检查


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"         # 等待中
    RUNNING = "running"         # 运行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消
    SKIPPED = "skipped"         # 已跳过


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
        
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class ScheduleConfig:
    """调度配置"""
    task_id: str
    task_type: TaskType
    cron_expression: str
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 300  # 秒
    timeout: int = 3600     # 秒
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class DailyScheduler:
    """每日调度器"""
    
    def __init__(
        self,
        data_service: DataService,
        strategy_service: StrategyService,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化调度器"""
        self.data_service = data_service
        self.strategy_service = strategy_service
        self.config = config or {}
        
        # 初始化调度器
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': False,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )
        
        # 任务管理
        self.task_results = {}
        self.running_tasks = {}
        self.schedule_configs = []
        
        # 策略组合器
        self.strategy_combiner = StrategyCombiner()
        
        # 初始化默认配置
        self._initialize_default_schedules()
        
        # 结果存储目录
        self.results_dir = Path(settings.DATA_DIR) / "scheduler_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("每日调度器初始化完成")
    
    def _initialize_default_schedules(self):
        """初始化默认调度任务"""
        default_schedules = [
            # 早盘数据更新 - 9:00
            ScheduleConfig(
                task_id="morning_data_update",
                task_type=TaskType.DATA_UPDATE,
                cron_expression="0 9 * * 1-5",  # 工作日9:00
                parameters={"update_type": "morning", "lookback_days": 1}
            ),
            
            # 早盘卖出策略 - 9:25
            ScheduleConfig(
                task_id="morning_sell_strategy",
                task_type=TaskType.STRATEGY_RUN,
                cron_expression="25 9 * * 1-5",  # 工作日9:25
                parameters={
                    "strategy_names": ["morning_sell"],
                    "mode": "live"
                }
            ),
            
            # 尾盘数据更新 - 14:30
            ScheduleConfig(
                task_id="evening_data_update",
                task_type=TaskType.DATA_UPDATE,
                cron_expression="30 14 * * 1-5",  # 工作日14:30
                parameters={"update_type": "evening", "lookback_days": 1}
            ),
            
            # 尾盘买入策略 - 14:45
            ScheduleConfig(
                task_id="evening_buy_strategy",
                task_type=TaskType.STRATEGY_RUN,
                cron_expression="45 14 * * 1-5",  # 工作日14:45
                parameters={
                    "strategy_names": ["evening_buy"],
                    "mode": "live"
                }
            ),
            
            # 收盘后数据更新 - 15:30
            ScheduleConfig(
                task_id="closing_data_update",
                task_type=TaskType.DATA_UPDATE,
                cron_expression="30 15 * * 1-5",  # 工作日15:30
                parameters={"update_type": "closing", "lookback_days": 1}
            ),
            
            # 每日回测 - 18:00
            ScheduleConfig(
                task_id="daily_backtest",
                task_type=TaskType.BACKTEST,
                cron_expression="0 18 * * 1-5",  # 工作日18:00
                parameters={
                    "strategy_names": ["evening_buy", "morning_sell"],
                    "lookback_days": 30
                }
            ),
            
            # 每日报告生成 - 19:00
            ScheduleConfig(
                task_id="daily_report",
                task_type=TaskType.REPORT_GENERATE,
                cron_expression="0 19 * * 1-5",  # 工作日19:00
                parameters={"report_type": "daily"}
            ),
            
            # 周末清理任务 - 周六 2:00
            ScheduleConfig(
                task_id="weekly_cleanup",
                task_type=TaskType.CLEANUP,
                cron_expression="0 2 * * 6",  # 周六2:00
                parameters={"cleanup_days": 30}
            ),
            
            # 健康检查 - 每小时
            ScheduleConfig(
                task_id="health_check",
                task_type=TaskType.HEALTH_CHECK,
                cron_expression="0 * * * *",  # 每小时
                parameters={}
            )
        ]
        
        self.schedule_configs.extend(default_schedules)
        logger.info(f"初始化了 {len(default_schedules)} 个默认调度任务")
    
    async def start(self):
        """启动调度器"""
        try:
            logger.info("启动每日调度器")
            
            # 注册所有调度任务
            for schedule_config in self.schedule_configs:
                if schedule_config.enabled:
                    await self._register_schedule(schedule_config)
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info(f"调度器已启动，注册了 {len(self.scheduler.get_jobs())} 个任务")
            
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止调度器"""
        try:
            logger.info("停止每日调度器")
            
            # 等待运行中的任务完成
            if self.running_tasks:
                logger.info(f"等待 {len(self.running_tasks)} 个任务完成")
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
            
            # 停止调度器
            self.scheduler.shutdown(wait=True)
            
            logger.info("调度器已停止")
            
        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
    
    async def _register_schedule(self, schedule_config: ScheduleConfig):
        """注册调度任务"""
        try:
            # 解析cron表达式
            cron_parts = schedule_config.cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError(f"无效的cron表达式: {schedule_config.cron_expression}")
            
            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4]
            )
            
            # 添加任务
            self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                id=schedule_config.task_id,
                args=[schedule_config],
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"注册调度任务: {schedule_config.task_id} - {schedule_config.cron_expression}")
            
        except Exception as e:
            logger.error(f"注册调度任务失败: {schedule_config.task_id} - {str(e)}")
    
    async def _execute_scheduled_task(self, schedule_config: ScheduleConfig):
        """执行调度任务"""
        task_id = f"{schedule_config.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"开始执行调度任务: {task_id}")
            
            # 创建任务结果记录
            task_result = TaskResult(
                task_id=task_id,
                task_type=schedule_config.task_type,
                status=TaskStatus.RUNNING,
                start_time=datetime.now()
            )
            
            self.task_results[task_id] = task_result
            
            # 执行任务
            if schedule_config.task_type == TaskType.STRATEGY_RUN:
                result_data = await self._execute_strategy_task(schedule_config.parameters)
            elif schedule_config.task_type == TaskType.DATA_UPDATE:
                result_data = await self._execute_data_update_task(schedule_config.parameters)
            elif schedule_config.task_type == TaskType.BACKTEST:
                result_data = await self._execute_backtest_task(schedule_config.parameters)
            elif schedule_config.task_type == TaskType.REPORT_GENERATE:
                result_data = await self._execute_report_task(schedule_config.parameters)
            elif schedule_config.task_type == TaskType.CLEANUP:
                result_data = await self._execute_cleanup_task(schedule_config.parameters)
            elif schedule_config.task_type == TaskType.HEALTH_CHECK:
                result_data = await self._execute_health_check_task(schedule_config.parameters)
            else:
                raise ValueError(f"不支持的任务类型: {schedule_config.task_type}")
            
            # 更新任务结果
            task_result.status = TaskStatus.COMPLETED
            task_result.end_time = datetime.now()
            task_result.result_data = result_data
            
            # 保存结果
            await self._save_task_result(task_result)
            
            logger.info(f"调度任务执行完成: {task_id}")
            
        except Exception as e:
            logger.error(f"调度任务执行失败: {task_id} - {str(e)}")
            
            # 更新失败状态
            if task_id in self.task_results:
                task_result = self.task_results[task_id]
                task_result.status = TaskStatus.FAILED
                task_result.end_time = datetime.now()
                task_result.error_message = str(e)
                
                await self._save_task_result(task_result)
    
    async def _execute_strategy_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略任务"""
        try:
            strategy_names = parameters.get('strategy_names', [])
            mode = parameters.get('mode', 'simulation')
            
            logger.info(f"执行策略任务: {strategy_names}, 模式: {mode}")
            
            # 获取股票池
            stock_codes = await self._get_stock_pool()
            
            # 获取股票数据
            stock_data_dict = {}
            for stock_code in stock_codes:
                try:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    
                    stock_data = await self.data_service.get_stock_data(
                        stock_code, start_date, end_date
                    )
                    
                    if not stock_data.empty:
                        stock_data_dict[stock_code] = stock_data
                        
                except Exception as e:
                    logger.warning(f"获取股票数据失败: {stock_code} - {str(e)}")
                    continue
            
            # 运行组合策略
            signals = await self.strategy_combiner.run_combined_strategy(
                stock_data_dict, strategy_names
            )
            
            result = {
                'strategy_names': strategy_names,
                'mode': mode,
                'stock_count': len(stock_data_dict),
                'signal_count': len(signals),
                'signals': signals,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行策略任务失败: {str(e)}")
            raise
    
    async def _execute_data_update_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据更新任务"""
        try:
            update_type = parameters.get('update_type', 'full')
            lookback_days = parameters.get('lookback_days', 1)
            
            logger.info(f"执行数据更新任务: {update_type}, 回看天数: {lookback_days}")
            
            # 获取股票池
            stock_codes = await self._get_stock_pool()
            
            updated_count = 0
            failed_count = 0
            
            # 更新股票数据
            for stock_code in stock_codes:
                try:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                    
                    # 这里应该调用数据服务的更新方法
                    # await self.data_service.update_stock_data(stock_code, start_date, end_date)
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.warning(f"更新股票数据失败: {stock_code} - {str(e)}")
                    failed_count += 1
                    continue
            
            result = {
                'update_type': update_type,
                'lookback_days': lookback_days,
                'total_stocks': len(stock_codes),
                'updated_count': updated_count,
                'failed_count': failed_count,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行数据更新任务失败: {str(e)}")
            raise
    
    async def _execute_backtest_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行回测任务"""
        try:
            strategy_names = parameters.get('strategy_names', [])
            lookback_days = parameters.get('lookback_days', 30)
            
            logger.info(f"执行回测任务: {strategy_names}, 回看天数: {lookback_days}")
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
            
            backtest_results = []
            
            for strategy_name in strategy_names:
                try:
                    result = await self.strategy_service.backtest_strategy(
                        strategy_name, start_date, end_date
                    )
                    backtest_results.append(result)
                    
                except Exception as e:
                    logger.warning(f"回测策略失败: {strategy_name} - {str(e)}")
                    continue
            
            result = {
                'strategy_names': strategy_names,
                'backtest_period': f"{start_date} 到 {end_date}",
                'backtest_results': backtest_results,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行回测任务失败: {str(e)}")
            raise
    
    async def _execute_report_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行报告生成任务"""
        try:
            report_type = parameters.get('report_type', 'daily')
            
            logger.info(f"执行报告生成任务: {report_type}")
            
            # 生成报告数据
            report_data = {
                'report_type': report_type,
                'generation_time': datetime.now().isoformat(),
                'summary': {
                    'total_signals': 0,
                    'successful_trades': 0,
                    'total_return': 0.0
                },
                'strategy_performance': [],
                'market_overview': {}
            }
            
            # TODO: 实现具体的报告生成逻辑
            
            result = {
                'report_type': report_type,
                'report_data': report_data,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行报告生成任务失败: {str(e)}")
            raise
    
    async def _execute_cleanup_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行清理任务"""
        try:
            cleanup_days = parameters.get('cleanup_days', 30)
            
            logger.info(f"执行清理任务: 清理 {cleanup_days} 天前的数据")
            
            cutoff_date = datetime.now() - timedelta(days=cleanup_days)
            
            # 清理任务结果
            cleaned_results = 0
            for task_id, task_result in list(self.task_results.items()):
                if task_result.start_time < cutoff_date:
                    del self.task_results[task_id]
                    cleaned_results += 1
            
            # 清理日志文件
            cleaned_files = 0
            if self.results_dir.exists():
                for file_path in self.results_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date.timestamp():
                        file_path.unlink()
                        cleaned_files += 1
            
            result = {
                'cleanup_days': cleanup_days,
                'cleaned_results': cleaned_results,
                'cleaned_files': cleaned_files,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行清理任务失败: {str(e)}")
            raise
    
    async def _execute_health_check_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行健康检查任务"""
        try:
            logger.info("执行健康检查任务")
            
            health_status = {
                'scheduler_status': 'running' if self.scheduler.running else 'stopped',
                'active_jobs': len(self.scheduler.get_jobs()),
                'running_tasks': len(self.running_tasks),
                'total_task_results': len(self.task_results),
                'memory_usage': 0,  # TODO: 实现内存使用检查
                'disk_usage': 0,    # TODO: 实现磁盘使用检查
                'last_check_time': datetime.now().isoformat()
            }
            
            # 检查最近任务执行情况
            recent_failures = 0
            recent_time = datetime.now() - timedelta(hours=24)
            
            for task_result in self.task_results.values():
                if (task_result.start_time > recent_time and 
                    task_result.status == TaskStatus.FAILED):
                    recent_failures += 1
            
            health_status['recent_failures'] = recent_failures
            health_status['health_score'] = max(0, 100 - recent_failures * 10)
            
            result = {
                'health_status': health_status,
                'execution_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"执行健康检查任务失败: {str(e)}")
            raise
    
    async def _get_stock_pool(self) -> List[str]:
        """获取股票池"""
        # 返回默认股票池
        return [
            "600000", "600001", "600002", "600003", "600004",
            "600005", "600006", "600007", "600008", "600009",
            "000001", "000002", "000003", "000004", "000005",
            "300001", "300002", "300003", "300004", "300005"
        ]
    
    async def _save_task_result(self, task_result: TaskResult):
        """保存任务结果"""
        try:
            result_file = self.results_dir / f"{task_result.task_id}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(task_result), f, ensure_ascii=False, indent=2, default=str)
            
            logger.debug(f"任务结果已保存: {result_file}")
            
        except Exception as e:
            logger.warning(f"保存任务结果失败: {str(e)}")
    
    async def run_task_manually(
        self,
        task_type: TaskType,
        parameters: Dict[str, Any]
    ) -> TaskResult:
        """手动运行任务"""
        task_id = f"manual_{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"手动运行任务: {task_id}")
            
            # 创建调度配置
            schedule_config = ScheduleConfig(
                task_id=task_id,
                task_type=task_type,
                cron_expression="",  # 手动任务不需要cron
                parameters=parameters
            )
            
            # 执行任务
            await self._execute_scheduled_task(schedule_config)
            
            return self.task_results.get(task_id)
            
        except Exception as e:
            logger.error(f"手动运行任务失败: {task_id} - {str(e)}")
            raise
    
    def get_task_results(
        self,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[TaskResult]:
        """获取任务结果"""
        results = list(self.task_results.values())
        
        # 过滤
        if task_type:
            results = [r for r in results if r.task_type == task_type]
        
        if status:
            results = [r for r in results if r.status == status]
        
        # 排序并限制数量
        results.sort(key=lambda x: x.start_time, reverse=True)
        
        return results[:limit]
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """获取调度状态"""
        jobs = self.scheduler.get_jobs()
        
        return {
            'scheduler_running': self.scheduler.running,
            'total_jobs': len(jobs),
            'enabled_schedules': len([s for s in self.schedule_configs if s.enabled]),
            'running_tasks': len(self.running_tasks),
            'total_task_results': len(self.task_results),
            'next_jobs': [
                {
                    'job_id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs[:5]  # 显示前5个即将执行的任务
            ]
        }
    
    def add_schedule(self, schedule_config: ScheduleConfig):
        """添加调度任务"""
        self.schedule_configs.append(schedule_config)
        
        if self.scheduler.running and schedule_config.enabled:
            asyncio.create_task(self._register_schedule(schedule_config))
        
        logger.info(f"添加调度任务: {schedule_config.task_id}")
    
    def remove_schedule(self, task_id: str):
        """移除调度任务"""
        # 从配置中移除
        self.schedule_configs = [
            s for s in self.schedule_configs if s.task_id != task_id
        ]
        
        # 从调度器中移除
        try:
            self.scheduler.remove_job(task_id)
        except Exception:
            pass  # 任务可能不存在
        
        logger.info(f"移除调度任务: {task_id}")
    
    def enable_schedule(self, task_id: str):
        """启用调度任务"""
        for schedule_config in self.schedule_configs:
            if schedule_config.task_id == task_id:
                schedule_config.enabled = True
                
                if self.scheduler.running:
                    asyncio.create_task(self._register_schedule(schedule_config))
                
                logger.info(f"启用调度任务: {task_id}")
                break
    
    def disable_schedule(self, task_id: str):
        """禁用调度任务"""
        for schedule_config in self.schedule_configs:
            if schedule_config.task_id == task_id:
                schedule_config.enabled = False
                
                try:
                    self.scheduler.remove_job(task_id)
                except Exception:
                    pass
                
                logger.info(f"禁用调度任务: {task_id}")
                break