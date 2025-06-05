from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import asyncio
from typing import Optional

from config.database import get_db
from backend.app.models.stock import Recommendation, Stock
from backend.app.services.strategy_service import StrategyService
from loguru import logger


class StockScheduler:
    """股票推荐定时任务调度器"""
    
    def __init__(self):
        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5分钟容错时间
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 尾盘买入策略 - 每个交易日14:55执行
        self.scheduler.add_job(
            func=self._run_end_of_day_strategy,
            trigger=CronTrigger(
                hour=14,
                minute=55,
                day_of_week='mon-fri'  # 周一到周五
            ),
            id='end_of_day_buy',
            name='尾盘买入策略',
            replace_existing=True
        )
        
        # 早盘卖出策略 - 每个交易日9:35执行
        self.scheduler.add_job(
            func=self._run_morning_exit_strategy,
            trigger=CronTrigger(
                hour=9,
                minute=35,
                day_of_week='mon-fri'  # 周一到周五
            ),
            id='morning_exit',
            name='早盘卖出策略',
            replace_existing=True
        )
        
        # 推荐清理任务 - 每天21:00清理过期推荐
        self.scheduler.add_job(
            func=self._cleanup_expired_recommendations,
            trigger=CronTrigger(
                hour=21,
                minute=0
            ),
            id='cleanup_recommendations',
            name='清理过期推荐',
            replace_existing=True
        )
        
        # 数据同步任务 - 每个交易日收盘后同步数据
        self.scheduler.add_job(
            func=self._sync_market_data,
            trigger=CronTrigger(
                hour=15,
                minute=30,
                day_of_week='mon-fri'
            ),
            id='sync_market_data',
            name='同步市场数据',
            replace_existing=True
        )
    
    async def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")
            
            # 打印已注册的任务
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"已注册任务: {job.name} (ID: {job.id}) - 下次执行: {job.next_run_time}")
                
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """获取任务状态"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger),
                    'func': job.func.__name__
                }
            return None
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}")
            return None
    
    def get_all_jobs(self) -> list:
        """获取所有任务状态"""
        try:
            jobs = self.scheduler.get_jobs()
            return [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger),
                    'func': job.func.__name__
                }
                for job in jobs
            ]
        except Exception as e:
            logger.error(f"获取任务列表失败: {str(e)}")
            return []
    
    async def run_job_now(self, job_id: str):
        """立即执行指定任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                await job.func()
                logger.info(f"手动执行任务成功: {job.name}")
            else:
                logger.warning(f"任务不存在: {job_id}")
        except Exception as e:
            logger.error(f"手动执行任务失败 {job_id}: {str(e)}")
            raise
    
    # 任务执行函数
    
    async def _run_end_of_day_strategy(self):
        """执行尾盘买入策略"""
        logger.info("开始执行尾盘买入策略定时任务")
        
        try:
            # 检查是否为交易日
            if not self._is_trading_day():
                logger.info("今日非交易日，跳过尾盘买入策略")
                return
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 获取活跃股票列表
                stock_codes = await self._get_active_stock_codes(db)
                
                if not stock_codes:
                    logger.warning("没有找到活跃股票，跳过策略执行")
                    return
                
                # 执行尾盘策略
                strategy_service = StrategyService(db)
                results = await strategy_service.execute_strategy(
                    strategy_name="end_of_day",
                    stock_codes=stock_codes,
                    parameters={
                        'consecutive_days': 2,
                        'volume_ratio': 1.5,
                        'min_confidence': 0.7
                    }
                )
                
                # 保存推荐结果
                saved_count = await self._save_recommendations(db, results, 'end_of_day')
                
                logger.info(f"尾盘买入策略执行完成，生成推荐 {saved_count} 条")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"执行尾盘买入策略失败: {str(e)}")
    
    async def _run_morning_exit_strategy(self):
        """执行早盘卖出策略"""
        logger.info("开始执行早盘卖出策略定时任务")
        
        try:
            # 检查是否为交易日
            if not self._is_trading_day():
                logger.info("今日非交易日，跳过早盘卖出策略")
                return
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 获取昨日买入的股票
                held_stocks = await self._get_held_stocks(db)
                
                if not held_stocks:
                    logger.info("没有持有股票，跳过早盘卖出策略")
                    return
                
                stock_codes = [stock['stock_code'] for stock in held_stocks]
                
                # 执行早盘卖出策略
                strategy_service = StrategyService(db)
                results = await strategy_service.execute_strategy(
                    strategy_name="morning_exit",
                    stock_codes=stock_codes,
                    parameters={
                        'profit_target': 0.05,
                        'stop_loss': 0.03,
                        'min_confidence': 0.6
                    }
                )
                
                # 保存卖出推荐
                saved_count = await self._save_recommendations(db, results, 'morning_exit')
                
                logger.info(f"早盘卖出策略执行完成，生成推荐 {saved_count} 条")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"执行早盘卖出策略失败: {str(e)}")
    
    async def _cleanup_expired_recommendations(self):
        """清理过期推荐"""
        logger.info("开始清理过期推荐")
        
        try:
            db = next(get_db())
            
            try:
                # 查找过期的推荐
                now = datetime.now()
                expired_recs = db.query(Recommendation).filter(
                    and_(
                        Recommendation.expires_at < now,
                        Recommendation.is_active == True
                    )
                ).all()
                
                # 标记为非活跃
                count = 0
                for rec in expired_recs:
                    rec.is_active = False
                    count += 1
                
                db.commit()
                
                logger.info(f"清理过期推荐完成，处理 {count} 条记录")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"清理过期推荐失败: {str(e)}")
    
    async def _sync_market_data(self):
        """同步市场数据"""
        logger.info("开始同步市场数据")
        
        try:
            # 这里可以调用数据同步服务
            # 例如：从tushare、新浪财经等获取最新数据
            
            # 暂时记录日志
            logger.info("市场数据同步完成（占位符）")
            
        except Exception as e:
            logger.error(f"同步市场数据失败: {str(e)}")
    
    # 辅助方法
    
    def _is_trading_day(self) -> bool:
        """检查是否为交易日"""
        now = datetime.now()
        
        # 简单检查：周一到周五
        # 实际应用中应该考虑节假日
        return now.weekday() < 5
    
    async def _get_active_stock_codes(self, db: Session) -> list:
        """获取活跃股票代码"""
        try:
            stocks = db.query(Stock).filter(
                Stock.is_active == True
            ).limit(1000).all()
            
            return [stock.code for stock in stocks]
            
        except Exception as e:
            logger.error(f"获取活跃股票失败: {str(e)}")
            return []
    
    async def _get_held_stocks(self, db: Session) -> list:
        """获取持有的股票"""
        try:
            # 获取昨日买入的推荐
            yesterday = datetime.now().date() - timedelta(days=1)
            
            held_recs = db.query(Recommendation).filter(
                and_(
                    Recommendation.recommendation_type == 'buy',
                    Recommendation.created_at >= yesterday,
                    Recommendation.is_active == True
                )
            ).all()
            
            return [
                {
                    'stock_code': rec.stock_code,
                    'recommendation_id': rec.id,
                    'buy_date': rec.created_at.date()
                }
                for rec in held_recs
            ]
            
        except Exception as e:
            logger.error(f"获取持有股票失败: {str(e)}")
            return []
    
    async def _save_recommendations(self, db: Session, results: list, strategy_name: str) -> int:
        """保存推荐结果"""
        saved_count = 0
        
        try:
            for result in results:
                if result.get('confidence', 0) >= 0.6:  # 最小置信度过滤
                    try:
                        recommendation = Recommendation(
                            stock_code=result['stock_code'],
                            recommendation_type=result['signal'],
                            strategy_name=strategy_name,
                            confidence_score=result['confidence'],
                            target_price=result.get('target_price'),
                            stop_loss_price=result.get('stop_loss'),
                            reason=result.get('reason', ''),
                            signal_type=result.get('signal_type'),
                            expected_return=result.get('expected_return'),
                            holding_period=result.get('holding_period'),
                            risk_level=result.get('risk_level', 'medium'),
                            created_at=datetime.now(),
                            expires_at=result.get('expires_at'),
                            is_active=True
                        )
                        
                        db.add(recommendation)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"保存推荐失败 {result['stock_code']}: {str(e)}")
                        continue
            
            db.commit()
            return saved_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量保存推荐失败: {str(e)}")
            return 0


# 全局调度器实例
scheduler_instance: Optional[StockScheduler] = None


def get_scheduler() -> StockScheduler:
    """获取调度器实例"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = StockScheduler()
    return scheduler_instance


async def start_scheduler():
    """启动调度器"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """停止调度器"""
    global scheduler_instance
    if scheduler_instance:
        await scheduler_instance.stop()
        scheduler_instance = None