from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
import json
import asyncio
import pandas as pd
import io
from pathlib import Path

from app.models.stock import Stock, StockPrice
from config.database import cache_manager
from config.settings import settings
from loguru import logger


class DataService:
    """数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_manager
        self.data_sources = {
            'tushare': None,
            'eastmoney': None,
            'sina': None,
            'local_csv': None
        }
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源"""
        try:
            # 初始化Tushare
            try:
                import tushare as ts
                from config.api_keys import TUSHARE_TOKEN
                if TUSHARE_TOKEN:
                    ts.set_token(TUSHARE_TOKEN)
                    self.data_sources['tushare'] = ts.pro_api()
                    logger.info("Tushare数据源初始化成功")
            except Exception as e:
                logger.warning(f"Tushare初始化失败: {str(e)}")
            
            # 初始化其他数据源
            self.data_sources['local_csv'] = True  # CSV总是可用
            
        except Exception as e:
            logger.error(f"数据源初始化失败: {str(e)}")
    
    async def get_data_sources(self) -> List[Dict[str, Any]]:
        """获取数据源列表和状态"""
        try:
            sources = []
            
            for source_name, source_instance in self.data_sources.items():
                status = "available" if source_instance else "unavailable"
                
                # 测试连接状态
                if source_instance and source_name != 'local_csv':
                    try:
                        # 简单的连接测试
                        await self._test_data_source_connection(source_name)
                        connection_status = "connected"
                    except:
                        connection_status = "disconnected"
                else:
                    connection_status = "local" if source_name == 'local_csv' else "disconnected"
                
                source_info = {
                    'name': source_name,
                    'display_name': self._get_source_display_name(source_name),
                    'status': status,
                    'connection_status': connection_status,
                    'description': self._get_source_description(source_name),
                    'supported_data_types': self._get_supported_data_types(source_name)
                }
                sources.append(source_info)
            
            return sources
            
        except Exception as e:
            logger.error(f"获取数据源列表失败: {str(e)}")
            raise
    
    async def sync_market_data(
        self,
        data_type: str = "daily",
        source: str = "auto",
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """同步市场数据"""
        try:
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # 选择数据源
            selected_source = await self._select_best_source(source)
            
            # 获取股票列表
            if not stock_codes:
                stock_codes = await self._get_active_stock_codes()
            
            # 同步数据
            sync_results = {
                'source': selected_source,
                'data_type': data_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_stocks': len(stock_codes),
                'success_count': 0,
                'failed_count': 0,
                'failed_stocks': [],
                'sync_time': datetime.now().isoformat()
            }
            
            for stock_code in stock_codes:
                try:
                    await self._sync_stock_data(
                        stock_code,
                        selected_source,
                        data_type,
                        start_date,
                        end_date
                    )
                    sync_results['success_count'] += 1
                except Exception as e:
                    sync_results['failed_count'] += 1
                    sync_results['failed_stocks'].append({
                        'stock_code': stock_code,
                        'error': str(e)
                    })
                    logger.warning(f"同步股票{stock_code}数据失败: {str(e)}")
            
            logger.info(f"市场数据同步完成: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"同步市场数据失败: {str(e)}")
            raise
    
    async def get_kline_data(
        self,
        stock_code: str,
        period: str = "daily",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=limit)
            
            # 从缓存获取
            cache_key = f"kline:{stock_code}:{period}:{start_date}:{end_date}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 从数据库获取
            query = self.db.query(StockPrice).filter(
                and_(
                    StockPrice.stock_code == stock_code,
                    StockPrice.trade_date >= start_date,
                    StockPrice.trade_date <= end_date
                )
            ).order_by(StockPrice.trade_date)
            
            prices = query.limit(limit).all()
            
            # 转换为K线格式
            kline_data = []
            for price in prices:
                kline_data.append({
                    'date': price.trade_date.isoformat(),
                    'open': price.open_price,
                    'high': price.high_price,
                    'low': price.low_price,
                    'close': price.close_price,
                    'volume': price.volume,
                    'amount': price.amount,
                    'turnover_rate': price.turnover_rate
                })
            
            # 缓存结果
            self.cache.set(
                cache_key,
                json.dumps(kline_data),
                expire=300  # 5分钟缓存
            )
            
            return kline_data
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {str(e)}")
            raise
    
    async def get_realtime_quotes(
        self,
        stock_codes: List[str]
    ) -> List[Dict[str, Any]]:
        """获取实时行情"""
        try:
            quotes = []
            
            for stock_code in stock_codes:
                # 从缓存获取
                cache_key = f"realtime:{stock_code}"
                cached_data = self.cache.get(cache_key)
                
                if cached_data:
                    quotes.append(json.loads(cached_data))
                    continue
                
                # 获取最新价格数据
                latest_price = self.db.query(StockPrice).filter(
                    StockPrice.stock_code == stock_code
                ).order_by(desc(StockPrice.trade_date)).first()
                
                if latest_price:
                    quote_data = {
                        'stock_code': stock_code,
                        'current_price': latest_price.close_price,
                        'open_price': latest_price.open_price,
                        'high_price': latest_price.high_price,
                        'low_price': latest_price.low_price,
                        'pre_close': latest_price.pre_close_price,
                        'volume': latest_price.volume,
                        'amount': latest_price.amount,
                        'turnover_rate': latest_price.turnover_rate,
                        'change': latest_price.close_price - (latest_price.pre_close_price or latest_price.close_price),
                        'change_percent': ((latest_price.close_price - (latest_price.pre_close_price or latest_price.close_price)) / (latest_price.pre_close_price or latest_price.close_price)) * 100,
                        'update_time': latest_price.trade_date.isoformat()
                    }
                    
                    quotes.append(quote_data)
                    
                    # 缓存结果
                    self.cache.set(
                        cache_key,
                        json.dumps(quote_data),
                        expire=60  # 1分钟缓存
                    )
            
            return quotes
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {str(e)}")
            raise
    
    async def get_fundamentals_data(
        self,
        stock_code: str,
        data_type: str = "basic"
    ) -> Dict[str, Any]:
        """获取基本面数据"""
        try:
            # 从缓存获取
            cache_key = f"fundamentals:{stock_code}:{data_type}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 获取股票基本信息
            stock = self.db.query(Stock).filter(Stock.code == stock_code).first()
            
            if not stock:
                raise ValueError(f"股票{stock_code}不存在")
            
            fundamentals = {
                'stock_code': stock_code,
                'stock_name': stock.name,
                'industry': stock.industry,
                'market': stock.market,
                'list_date': stock.list_date.isoformat() if stock.list_date else None,
                'market_cap': stock.market_cap,
                'pe_ratio': stock.pe_ratio,
                'pb_ratio': stock.pb_ratio,
                'update_time': datetime.now().isoformat()
            }
            
            # 根据数据类型获取更多信息
            if data_type == "financial":
                # 这里可以添加财务数据
                fundamentals.update({
                    'revenue': None,
                    'profit': None,
                    'roe': None,
                    'roa': None,
                    'debt_ratio': None
                })
            
            # 缓存结果
            self.cache.set(
                cache_key,
                json.dumps(fundamentals),
                expire=3600  # 1小时缓存
            )
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"获取基本面数据失败: {str(e)}")
            raise
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        try:
            # 从缓存获取
            cache_key = "market_overview"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            today = date.today()
            
            # 统计市场数据
            total_stocks = self.db.query(func.count(Stock.code)).scalar()
            
            # 今日交易统计
            today_prices = self.db.query(
                func.count(StockPrice.stock_code),
                func.sum(StockPrice.volume),
                func.sum(StockPrice.amount)
            ).filter(StockPrice.trade_date == today).first()
            
            trading_stocks = today_prices[0] or 0
            total_volume = today_prices[1] or 0
            total_amount = today_prices[2] or 0
            
            # 涨跌统计
            price_changes = self.db.query(
                StockPrice.close_price,
                StockPrice.pre_close_price
            ).filter(StockPrice.trade_date == today).all()
            
            rising = falling = unchanged = 0
            for close, pre_close in price_changes:
                if close > (pre_close or close):
                    rising += 1
                elif close < (pre_close or close):
                    falling += 1
                else:
                    unchanged += 1
            
            overview = {
                'total_stocks': total_stocks,
                'trading_stocks': trading_stocks,
                'rising_stocks': rising,
                'falling_stocks': falling,
                'unchanged_stocks': unchanged,
                'total_volume': total_volume,
                'total_amount': total_amount,
                'update_time': datetime.now().isoformat()
            }
            
            # 缓存结果
            self.cache.set(
                cache_key,
                json.dumps(overview),
                expire=300  # 5分钟缓存
            )
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {str(e)}")
            raise
    
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """获取市场指数"""
        try:
            # 主要指数代码
            index_codes = ['000001.SH', '399001.SZ', '399006.SZ']  # 上证指数、深证成指、创业板指
            
            indices = []
            for index_code in index_codes:
                # 获取指数最新数据
                latest_data = self.db.query(StockPrice).filter(
                    StockPrice.stock_code == index_code
                ).order_by(desc(StockPrice.trade_date)).first()
                
                if latest_data:
                    change = latest_data.close_price - (latest_data.pre_close_price or latest_data.close_price)
                    change_percent = (change / (latest_data.pre_close_price or latest_data.close_price)) * 100
                    
                    index_info = {
                        'code': index_code,
                        'name': self._get_index_name(index_code),
                        'current_value': latest_data.close_price,
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'volume': latest_data.volume,
                        'amount': latest_data.amount,
                        'update_time': latest_data.trade_date.isoformat()
                    }
                    indices.append(index_info)
            
            return indices
            
        except Exception as e:
            logger.error(f"获取市场指数失败: {str(e)}")
            raise
    
    async def get_money_flow(
        self,
        stock_code: Optional[str] = None,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """获取资金流向"""
        try:
            # 这里需要扩展资金流向数据表
            # 暂时返回模拟数据
            money_flow = {
                'stock_code': stock_code,
                'period': period,
                'main_inflow': 0,
                'main_outflow': 0,
                'retail_inflow': 0,
                'retail_outflow': 0,
                'net_inflow': 0,
                'update_time': datetime.now().isoformat()
            }
            
            return money_flow
            
        except Exception as e:
            logger.error(f"获取资金流向失败: {str(e)}")
            raise
    
    async def upload_csv_data(
        self,
        file_content: bytes,
        data_type: str = "price",
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """上传CSV数据"""
        try:
            # 解析CSV数据
            csv_data = io.StringIO(file_content.decode(encoding))
            df = pd.read_csv(csv_data)
            
            # 验证数据格式
            required_columns = self._get_required_columns(data_type)
            missing_columns = set(required_columns) - set(df.columns)
            
            if missing_columns:
                raise ValueError(f"缺少必要列: {missing_columns}")
            
            # 导入数据
            import_results = {
                'data_type': data_type,
                'total_rows': len(df),
                'success_count': 0,
                'failed_count': 0,
                'errors': [],
                'import_time': datetime.now().isoformat()
            }
            
            for index, row in df.iterrows():
                try:
                    await self._import_csv_row(row, data_type)
                    import_results['success_count'] += 1
                except Exception as e:
                    import_results['failed_count'] += 1
                    import_results['errors'].append({
                        'row': index + 1,
                        'error': str(e)
                    })
            
            logger.info(f"CSV数据导入完成: {import_results}")
            return import_results
            
        except Exception as e:
            logger.error(f"上传CSV数据失败: {str(e)}")
            raise
    
    async def export_csv_data(
        self,
        data_type: str = "price",
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> bytes:
        """导出CSV数据"""
        try:
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # 构建查询
            query = self.db.query(StockPrice).filter(
                and_(
                    StockPrice.trade_date >= start_date,
                    StockPrice.trade_date <= end_date
                )
            )
            
            if stock_codes:
                query = query.filter(StockPrice.stock_code.in_(stock_codes))
            
            # 获取数据
            prices = query.order_by(
                StockPrice.stock_code,
                StockPrice.trade_date
            ).all()
            
            # 转换为DataFrame
            data = []
            for price in prices:
                data.append({
                    'stock_code': price.stock_code,
                    'trade_date': price.trade_date.isoformat(),
                    'open_price': price.open_price,
                    'high_price': price.high_price,
                    'low_price': price.low_price,
                    'close_price': price.close_price,
                    'volume': price.volume,
                    'amount': price.amount,
                    'turnover_rate': price.turnover_rate
                })
            
            df = pd.DataFrame(data)
            
            # 转换为CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            return csv_buffer.getvalue().encode('utf-8')
            
        except Exception as e:
            logger.error(f"导出CSV数据失败: {str(e)}")
            raise
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            # 获取缓存统计信息
            cache_info = {
                'cache_type': 'Redis',
                'total_keys': 0,
                'memory_usage': 0,
                'hit_rate': 0,
                'categories': {}
            }
            
            # 这里需要根据实际的缓存实现来获取统计信息
            return cache_info
            
        except Exception as e:
            logger.error(f"获取缓存信息失败: {str(e)}")
            raise
    
    async def clear_cache(
        self,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """清理缓存"""
        try:
            if pattern:
                # 清理匹配模式的缓存
                cleared_count = self.cache.delete_pattern(pattern)
            else:
                # 清理所有缓存
                cleared_count = self.cache.clear_all()
            
            result = {
                'pattern': pattern or 'all',
                'cleared_count': cleared_count,
                'cleared_at': datetime.now().isoformat()
            }
            
            logger.info(f"缓存清理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
            raise
    
    async def get_data_quality_report(self) -> Dict[str, Any]:
        """获取数据质量报告"""
        try:
            # 统计数据质量指标
            total_stocks = self.db.query(func.count(Stock.code)).scalar()
            
            # 最近数据覆盖率
            recent_date = date.today() - timedelta(days=1)
            recent_data_count = self.db.query(
                func.count(StockPrice.stock_code.distinct())
            ).filter(StockPrice.trade_date == recent_date).scalar()
            
            coverage_rate = (recent_data_count / total_stocks) * 100 if total_stocks > 0 else 0
            
            # 数据完整性检查
            incomplete_data = self.db.query(
                func.count(StockPrice.id)
            ).filter(
                or_(
                    StockPrice.open_price.is_(None),
                    StockPrice.close_price.is_(None),
                    StockPrice.volume.is_(None)
                )
            ).scalar()
            
            # 数据时效性
            latest_data_date = self.db.query(
                func.max(StockPrice.trade_date)
            ).scalar()
            
            days_behind = (date.today() - latest_data_date).days if latest_data_date else None
            
            quality_report = {
                'total_stocks': total_stocks,
                'recent_coverage_rate': round(coverage_rate, 2),
                'incomplete_records': incomplete_data,
                'latest_data_date': latest_data_date.isoformat() if latest_data_date else None,
                'days_behind': days_behind,
                'data_sources_status': await self.get_data_sources(),
                'report_time': datetime.now().isoformat()
            }
            
            return quality_report
            
        except Exception as e:
            logger.error(f"获取数据质量报告失败: {str(e)}")
            raise
    
    # 辅助方法
    async def _test_data_source_connection(self, source_name: str) -> bool:
        """测试数据源连接"""
        try:
            if source_name == 'tushare' and self.data_sources['tushare']:
                # 测试Tushare连接
                self.data_sources['tushare'].stock_basic(list_status='L', limit=1)
                return True
            return False
        except:
            return False
    
    def _get_source_display_name(self, source_name: str) -> str:
        """获取数据源显示名称"""
        names = {
            'tushare': 'Tushare',
            'eastmoney': '东方财富',
            'sina': '新浪财经',
            'local_csv': '本地CSV'
        }
        return names.get(source_name, source_name)
    
    def _get_source_description(self, source_name: str) -> str:
        """获取数据源描述"""
        descriptions = {
            'tushare': '专业的金融数据接口',
            'eastmoney': '东方财富网数据接口',
            'sina': '新浪财经数据接口',
            'local_csv': '本地CSV文件数据'
        }
        return descriptions.get(source_name, '')
    
    def _get_supported_data_types(self, source_name: str) -> List[str]:
        """获取支持的数据类型"""
        types = {
            'tushare': ['daily', 'basic', 'financial', 'realtime'],
            'eastmoney': ['daily', 'realtime'],
            'sina': ['realtime'],
            'local_csv': ['daily', 'basic']
        }
        return types.get(source_name, [])
    
    async def _select_best_source(self, preferred_source: str) -> str:
        """选择最佳数据源"""
        if preferred_source != 'auto' and self.data_sources.get(preferred_source):
            return preferred_source
        
        # 按优先级选择可用数据源
        priority_sources = ['tushare', 'eastmoney', 'sina', 'local_csv']
        for source in priority_sources:
            if self.data_sources.get(source):
                return source
        
        return 'local_csv'  # 默认使用本地CSV
    
    async def _get_active_stock_codes(self) -> List[str]:
        """获取活跃股票代码列表"""
        stocks = self.db.query(Stock.code).filter(
            Stock.list_date <= date.today()
        ).limit(1000).all()
        
        return [stock[0] for stock in stocks]
    
    async def _sync_stock_data(
        self,
        stock_code: str,
        source: str,
        data_type: str,
        start_date: date,
        end_date: date
    ):
        """同步单个股票数据"""
        try:
            if source == 'tushare' and self.data_sources['tushare']:
                await self._sync_from_tushare(stock_code, data_type, start_date, end_date)
            elif source == 'local_csv':
                # 从本地CSV同步(如果有的话)
                pass
            else:
                raise ValueError(f"不支持的数据源: {source}")
                
        except Exception as e:
            logger.error(f"同步股票{stock_code}数据失败: {str(e)}")
            raise
    
    async def _sync_from_tushare(
        self,
        stock_code: str,
        data_type: str,
        start_date: date,
        end_date: date
    ):
        """从Tushare同步数据"""
        try:
            if data_type == 'daily':
                # 获取日线数据
                df = self.data_sources['tushare'].daily(
                    ts_code=stock_code,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )
                
                # 保存到数据库
                for _, row in df.iterrows():
                    price_data = StockPrice(
                        stock_code=row['ts_code'],
                        trade_date=datetime.strptime(row['trade_date'], '%Y%m%d').date(),
                        open_price=row['open'],
                        high_price=row['high'],
                        low_price=row['low'],
                        close_price=row['close'],
                        pre_close_price=row['pre_close'],
                        volume=row['vol'],
                        amount=row['amount']
                    )
                    
                    # 检查是否已存在
                    existing = self.db.query(StockPrice).filter(
                        and_(
                            StockPrice.stock_code == price_data.stock_code,
                            StockPrice.trade_date == price_data.trade_date
                        )
                    ).first()
                    
                    if not existing:
                        self.db.add(price_data)
                
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            raise
    
    def _get_index_name(self, index_code: str) -> str:
        """获取指数名称"""
        names = {
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指'
        }
        return names.get(index_code, index_code)
    
    def _get_required_columns(self, data_type: str) -> List[str]:
        """获取必要的列名"""
        columns = {
            'price': ['stock_code', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'],
            'basic': ['stock_code', 'name', 'industry', 'market']
        }
        return columns.get(data_type, [])
    
    async def _import_csv_row(self, row: pd.Series, data_type: str):
        """导入CSV行数据"""
        try:
            if data_type == 'price':
                price_data = StockPrice(
                    stock_code=row['stock_code'],
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    open_price=float(row['open_price']),
                    high_price=float(row['high_price']),
                    low_price=float(row['low_price']),
                    close_price=float(row['close_price']),
                    volume=int(row['volume']) if pd.notna(row['volume']) else None,
                    amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else None
                )
                
                # 检查是否已存在
                existing = self.db.query(StockPrice).filter(
                    and_(
                        StockPrice.stock_code == price_data.stock_code,
                        StockPrice.trade_date == price_data.trade_date
                    )
                ).first()
                
                if not existing:
                    self.db.add(price_data)
                    self.db.commit()
                    
        except Exception as e:
            self.db.rollback()
            raise