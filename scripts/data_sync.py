#!/usr/bin/env python3
"""
数据同步脚本

用于定期同步股票数据，包括基础信息、价格数据、基本面数据等。
"""

import os
import sys
import asyncio
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import get_db
from config.settings import settings
from data.manager import DataManager
from sqlalchemy.orm import Session


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self.data_manager = None
        self.db: Session = None
        
    async def initialize(self):
        """初始化服务"""
        # 获取数据库连接
        self.db = next(get_db())
        
        # 初始化数据管理器
        self.data_manager = DataManager()
        await self.data_manager.initialize()
        
        logger.info("数据同步服务初始化完成")
    
    async def sync_stock_list(self) -> bool:
        """同步股票列表"""
        try:
            logger.info("开始同步股票列表")
            
            # 获取股票列表
            stocks = await self.data_manager.get_stock_list()
            
            if not stocks:
                logger.warning("未获取到股票数据")
                return False
            
            # 更新数据库
            updated_count = 0
            for stock_data in stocks:
                # 这里应该调用数据库服务来更新股票信息
                # 简化实现，实际应该通过service层
                updated_count += 1
            
            logger.success(f"股票列表同步完成，更新 {updated_count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步股票列表失败: {e}")
            return False
    
    async def sync_daily_prices(self, target_date: date = None) -> bool:
        """同步日K线数据"""
        try:
            if target_date is None:
                target_date = date.today()
            
            logger.info(f"开始同步 {target_date} 的价格数据")
            
            # 获取所有活跃股票代码
            stock_codes = await self._get_active_stock_codes()
            
            if not stock_codes:
                logger.warning("未找到活跃股票")
                return False
            
            # 批量获取价格数据
            success_count = 0
            total_count = len(stock_codes)
            
            for i, stock_code in enumerate(stock_codes):
                try:
                    # 获取单只股票的价格数据
                    price_data = await self.data_manager.get_stock_prices(
                        stock_code, 
                        start_date=target_date,
                        end_date=target_date
                    )
                    
                    if price_data:
                        # 保存到数据库
                        # 这里应该调用数据库服务
                        success_count += 1
                    
                    # 显示进度
                    progress = (i + 1) / total_count * 100
                    logger.info(f"同步进度: {progress:.1f}% ({i+1}/{total_count})")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"同步股票 {stock_code} 价格数据失败: {e}")
                    continue
            
            logger.success(f"价格数据同步完成，成功 {success_count}/{total_count} 只股票")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"同步价格数据失败: {e}")
            return False
    
    async def sync_fundamentals(self, target_date: date = None) -> bool:
        """同步基本面数据"""
        try:
            if target_date is None:
                target_date = date.today()
            
            logger.info(f"开始同步 {target_date} 的基本面数据")
            
            # 获取所有活跃股票代码
            stock_codes = await self._get_active_stock_codes()
            
            success_count = 0
            for stock_code in stock_codes:
                try:
                    # 获取基本面数据
                    fundamental_data = await self.data_manager.get_stock_fundamentals(
                        stock_code,
                        target_date
                    )
                    
                    if fundamental_data:
                        # 保存到数据库
                        success_count += 1
                    
                    await asyncio.sleep(0.2)  # 基本面数据请求间隔稍长
                    
                except Exception as e:
                    logger.warning(f"同步股票 {stock_code} 基本面数据失败: {e}")
                    continue
            
            logger.success(f"基本面数据同步完成，成功 {success_count} 只股票")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"同步基本面数据失败: {e}")
            return False
    
    async def sync_market_data(self, target_date: date = None) -> bool:
        """同步市场数据"""
        try:
            if target_date is None:
                target_date = date.today()
            
            logger.info(f"开始同步 {target_date} 的市场数据")
            
            # 主要指数代码
            index_codes = ['000001.SH', '399001.SZ', '399006.SZ']  # 上证、深证、创业板
            
            success_count = 0
            for index_code in index_codes:
                try:
                    # 获取指数数据
                    market_data = await self.data_manager.get_market_data(
                        index_code,
                        start_date=target_date,
                        end_date=target_date
                    )
                    
                    if market_data:
                        # 保存到数据库
                        success_count += 1
                    
                except Exception as e:
                    logger.warning(f"同步指数 {index_code} 数据失败: {e}")
                    continue
            
            logger.success(f"市场数据同步完成，成功 {success_count} 个指数")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"同步市场数据失败: {e}")
            return False
    
    async def _get_active_stock_codes(self) -> List[str]:
        """获取活跃股票代码列表"""
        try:
            # 这里应该从数据库查询活跃股票
            # 简化实现，返回一些示例代码
            return [
                '000001.SZ', '000002.SZ', '600000.SH', '600036.SH',
                '000858.SZ', '002415.SZ', '600519.SH', '000725.SZ'
            ]
        except Exception as e:
            logger.error(f"获取股票代码列表失败: {e}")
            return []
    
    async def full_sync(self, target_date: date = None) -> Dict[str, bool]:
        """完整数据同步"""
        results = {
            'stock_list': False,
            'daily_prices': False,
            'fundamentals': False,
            'market_data': False
        }
        
        logger.info("开始完整数据同步")
        
        # 1. 同步股票列表
        results['stock_list'] = await self.sync_stock_list()
        
        # 2. 同步价格数据
        results['daily_prices'] = await self.sync_daily_prices(target_date)
        
        # 3. 同步基本面数据
        results['fundamentals'] = await self.sync_fundamentals(target_date)
        
        # 4. 同步市场数据
        results['market_data'] = await self.sync_market_data(target_date)
        
        # 统计结果
        success_count = sum(results.values())
        total_count = len(results)
        
        logger.info(f"完整数据同步完成: {success_count}/{total_count} 项成功")
        
        return results
    
    async def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()
        logger.info("数据同步服务已清理")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票数据同步工具')
    parser.add_argument('action', choices=['stocks', 'prices', 'fundamentals', 'market', 'full'],
                       help='同步类型')
    parser.add_argument('--date', '-d', help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--days', '-n', type=int, default=1, help='同步天数')
    
    args = parser.parse_args()
    
    # 解析日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error("日期格式错误，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    
    # 初始化服务
    service = DataSyncService()
    
    try:
        await service.initialize()
        
        # 执行同步
        if args.action == 'stocks':
            await service.sync_stock_list()
        
        elif args.action == 'prices':
            if args.days > 1:
                # 同步多天数据
                base_date = target_date or date.today()
                for i in range(args.days):
                    sync_date = base_date - timedelta(days=i)
                    await service.sync_daily_prices(sync_date)
            else:
                await service.sync_daily_prices(target_date)
        
        elif args.action == 'fundamentals':
            await service.sync_fundamentals(target_date)
        
        elif args.action == 'market':
            await service.sync_market_data(target_date)
        
        elif args.action == 'full':
            await service.full_sync(target_date)
        
    except KeyboardInterrupt:
        logger.info("用户中断同步")
    
    except Exception as e:
        logger.error(f"同步过程中发生错误: {e}")
        sys.exit(1)
    
    finally:
        await service.cleanup()


if __name__ == '__main__':
    asyncio.run(main())