from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import json
import asyncio

from backend.app.models.stock import (
    Stock, StockPrice, StockResponse, StockPriceResponse,
    StockListResponse, MarketOverview, TechnicalIndicators
)
from config.database import cache_manager
from config.settings import settings
from loguru import logger


class StockService:
    """股票服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_manager
    
    async def get_stock_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        market: Optional[str] = None,
        sort_by: str = "market_cap",
        sort_order: str = "desc"
    ) -> StockListResponse:
        """获取股票列表"""
        try:
            # 构建查询
            query = self.db.query(Stock)
            
            # 搜索条件
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Stock.code.like(search_pattern),
                        Stock.name.like(search_pattern),
                        Stock.pinyin.like(search_pattern)
                    )
                )
            
            # 行业筛选
            if industry:
                query = query.filter(Stock.industry == industry)
            
            # 市场筛选
            if market:
                query = query.filter(Stock.market == market)
            
            # 排序
            if hasattr(Stock, sort_by):
                order_column = getattr(Stock, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)
            
            # 总数统计
            total = query.count()
            
            # 分页
            offset = (page - 1) * size
            stocks = query.offset(offset).limit(size).all()
            
            # 获取当前价格信息
            stock_responses = []
            for stock in stocks:
                price_info = await self._get_current_price_info(stock.code)
                stock_data = StockResponse(
                    id=stock.id,
                    code=stock.code,
                    name=stock.name,
                    industry=stock.industry,
                    market=stock.market,
                    sector=stock.sector,
                    list_date=stock.list_date,
                    is_active=stock.is_active,
                    created_at=stock.created_at,
                    updated_at=stock.updated_at,
                    market_cap=price_info.get('market_cap'),
                    pe_ratio=price_info.get('pe_ratio'),
                    pb_ratio=price_info.get('pb_ratio'),
                    price=price_info.get('current_price'),
                    change=price_info.get('price_change'),
                    change_percent=price_info.get('price_change_percent'),
                    volume=price_info.get('volume'),
                    turnover=price_info.get('turnover_rate')
                )
                stock_responses.append(stock_data)
            
            return StockListResponse(
                items=stock_responses,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            raise
    
    async def get_stock_detail(self, stock_code: str) -> Optional[StockResponse]:
        """获取股票详细信息"""
        try:
            # 从缓存获取
            cache_key = f"stock_detail:{stock_code}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return StockResponse.parse_raw(cached_data)
            
            # 从数据库获取
            stock = self.db.query(Stock).filter(Stock.code == stock_code).first()
            
            if not stock:
                return None
            
            # 获取当前价格信息
            price_info = await self._get_current_price_info(stock_code)
            
            stock_data = StockResponse(
                id=stock.id,
                code=stock.code,
                name=stock.name,
                industry=stock.industry,
                market=stock.market,
                sector=stock.sector,
                list_date=stock.list_date,
                is_active=stock.is_active,
                created_at=stock.created_at,
                updated_at=stock.updated_at,
                market_cap=price_info.get('market_cap'),
                pe_ratio=price_info.get('pe_ratio'),
                pb_ratio=price_info.get('pb_ratio'),
                current_price=price_info.get('current_price'),
                price_change=price_info.get('price_change'),
                price_change_percent=price_info.get('price_change_percent'),
                volume=price_info.get('volume'),
                turnover_rate=price_info.get('turnover_rate')
            )
            
            # 缓存结果
            self.cache.set(
                cache_key,
                stock_data.json(),
                expire=300  # 5分钟缓存
            )
            
            return stock_data
            
        except Exception as e:
            logger.error(f"获取股票详情失败: {str(e)}")
            raise
    
    async def get_stock_price_history(
        self,
        stock_code: str,
        start_date: date,
        end_date: Optional[date] = None,
        period: str = "daily"
    ) -> List[StockPriceResponse]:
        """获取股票价格历史"""
        try:
            if not end_date:
                end_date = date.today()
            
            # 构建查询
            query = self.db.query(StockPrice).filter(
                and_(
                    StockPrice.stock_code == stock_code,
                    StockPrice.trade_date >= start_date,
                    StockPrice.trade_date <= end_date
                )
            ).order_by(StockPrice.trade_date)
            
            prices = query.all()
            
            # 根据周期聚合数据
            if period == "weekly":
                prices = self._aggregate_weekly_data(prices)
            elif period == "monthly":
                prices = self._aggregate_monthly_data(prices)
            
            return [StockPriceResponse.from_orm(price) for price in prices]
            
        except Exception as e:
            logger.error(f"获取股票价格历史失败: {str(e)}")
            raise
    
    async def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """获取当前价格"""
        try:
            return await self._get_current_price_info(stock_code)
        except Exception as e:
            logger.error(f"获取当前价格失败: {str(e)}")
            raise
    
    async def get_technical_indicators(
        self,
        stock_code: str,
        period: int = 20
    ) -> TechnicalIndicators:
        """获取技术指标"""
        try:
            # 获取最近的价格数据
            prices = self.db.query(StockPrice).filter(
                StockPrice.stock_code == stock_code
            ).order_by(desc(StockPrice.trade_date)).limit(period * 2).all()
            
            if len(prices) < period:
                raise ValueError(f"数据不足，需要至少{period}个交易日的数据")
            
            # 计算技术指标
            indicators = self._calculate_technical_indicators(prices, period)
            
            return TechnicalIndicators(**indicators)
            
        except Exception as e:
            logger.error(f"获取技术指标失败: {str(e)}")
            raise
    
    async def get_fundamentals(self, stock_code: str) -> Dict[str, Any]:
        """获取基本面数据"""
        try:
            # 从缓存获取
            cache_key = f"fundamentals:{stock_code}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 从数据库获取股票基本信息
            stock = self.db.query(Stock).filter(Stock.code == stock_code).first()
            
            if not stock:
                raise ValueError(f"股票{stock_code}不存在")
            
            # 获取最新财务数据(这里需要扩展财务数据表)
            fundamentals = {
                "stock_code": stock_code,
                "stock_name": stock.name,
                "market_cap": stock.market_cap,
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "industry": stock.industry,
                "market": stock.market,
                "list_date": stock.list_date.isoformat() if stock.list_date else None,
                # 这里可以添加更多财务指标
                "roe": None,  # 净资产收益率
                "roa": None,  # 总资产收益率
                "debt_ratio": None,  # 资产负债率
                "current_ratio": None,  # 流动比率
                "quick_ratio": None,  # 速动比率
                "gross_margin": None,  # 毛利率
                "net_margin": None,  # 净利率
                "revenue_growth": None,  # 营收增长率
                "profit_growth": None,  # 利润增长率
            }
            
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
    
    async def get_market_overview(self) -> MarketOverview:
        """获取市场概况"""
        try:
            # 从缓存获取
            cache_key = "market_overview"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return MarketOverview.parse_raw(cached_data)
            
            # 计算市场统计数据
            today = date.today()
            
            # 获取今日交易的股票数量
            total_stocks = self.db.query(func.count(Stock.code)).scalar()
            
            # 获取今日有价格数据的股票
            trading_stocks = self.db.query(
                func.count(StockPrice.stock_code.distinct())
            ).filter(StockPrice.trade_date == today).scalar() or 0
            
            # 计算涨跌统计
            price_changes = self.db.query(
                StockPrice.stock_code,
                StockPrice.close_price,
                StockPrice.pre_close_price
            ).filter(StockPrice.trade_date == today).all()
            
            rising_count = 0
            falling_count = 0
            unchanged_count = 0
            
            for _, close, pre_close in price_changes:
                if close > pre_close:
                    rising_count += 1
                elif close < pre_close:
                    falling_count += 1
                else:
                    unchanged_count += 1
            
            # 计算总成交额
            total_volume = self.db.query(
                func.sum(StockPrice.volume * StockPrice.close_price)
            ).filter(StockPrice.trade_date == today).scalar() or 0
            
            overview = MarketOverview(
                total_stocks=total_stocks,
                trading_stocks=trading_stocks,
                rising_stocks=rising_count,
                falling_stocks=falling_count,
                unchanged_stocks=unchanged_count,
                total_volume=total_volume,
                update_time=datetime.now()
            )
            
            # 缓存结果
            self.cache.set(
                cache_key,
                overview.json(),
                expire=300  # 5分钟缓存
            )
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概况失败: {str(e)}")
            raise
    
    async def get_industries(self) -> List[str]:
        """获取行业列表"""
        try:
            # 从缓存获取
            cache_key = "industries"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 从数据库获取
            industries = self.db.query(
                Stock.industry
            ).distinct().filter(
                Stock.industry.isnot(None)
            ).all()
            
            industry_list = [industry[0] for industry in industries if industry[0]]
            industry_list.sort()
            
            # 缓存结果
            self.cache.set(
                cache_key,
                json.dumps(industry_list),
                expire=3600  # 1小时缓存
            )
            
            return industry_list
            
        except Exception as e:
            logger.error(f"获取行业列表失败: {str(e)}")
            raise
    
    async def get_sectors(self) -> List[str]:
        """获取板块列表"""
        try:
            # 这里可以扩展板块概念表
            # 暂时返回市场分类
            markets = self.db.query(
                Stock.market
            ).distinct().filter(
                Stock.market.isnot(None)
            ).all()
            
            return [market[0] for market in markets if market[0]]
            
        except Exception as e:
            logger.error(f"获取板块列表失败: {str(e)}")
            raise
    
    async def get_gainers_losers(
        self,
        limit: int = 10,
        sort_type: str = "price_change_percent"
    ) -> Dict[str, List[StockResponse]]:
        """获取涨跌幅榜"""
        try:
            today = date.today()
            
            # 获取今日价格数据
            price_query = self.db.query(
                StockPrice.stock_code,
                StockPrice.close_price,
                StockPrice.pre_close_price,
                StockPrice.volume,
                ((StockPrice.close_price - StockPrice.pre_close_price) / StockPrice.pre_close_price * 100).label('change_percent')
            ).filter(StockPrice.trade_date == today)
            
            # 获取涨幅榜
            gainers_data = price_query.order_by(
                desc(text('change_percent'))
            ).limit(limit).all()
            
            # 获取跌幅榜
            losers_data = price_query.order_by(
                text('change_percent')
            ).limit(limit).all()
            
            # 转换为响应格式
            gainers = await self._convert_to_stock_responses(gainers_data)
            losers = await self._convert_to_stock_responses(losers_data)
            
            return {
                "gainers": gainers,
                "losers": losers
            }
            
        except Exception as e:
            logger.error(f"获取涨跌幅榜失败: {str(e)}")
            raise
    
    async def get_volume_leaders(self, limit: int = 10) -> List[StockResponse]:
        """获取成交量榜"""
        try:
            today = date.today()
            
            # 获取成交量排行
            volume_data = self.db.query(
                StockPrice.stock_code,
                StockPrice.close_price,
                StockPrice.pre_close_price,
                StockPrice.volume
            ).filter(
                StockPrice.trade_date == today
            ).order_by(
                desc(StockPrice.volume)
            ).limit(limit).all()
            
            return await self._convert_to_stock_responses(volume_data)
            
        except Exception as e:
            logger.error(f"获取成交量榜失败: {str(e)}")
            raise
    
    async def sync_stock_data(self, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """同步股票数据"""
        try:
            # 这里应该调用数据同步服务
            # 暂时返回模拟结果
            result = {
                "synced_at": datetime.now().isoformat(),
                "stock_code": stock_code or "all",
                "status": "success",
                "message": "数据同步完成"
            }
            
            logger.info(f"股票数据同步完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"股票数据同步失败: {str(e)}")
            raise
    
    async def _get_current_price_info(self, stock_code: str) -> Dict[str, Any]:
        """获取当前价格信息"""
        try:
            # 尝试从缓存获取
            cache_key = f"current_price:{stock_code}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 从数据库获取最新价格
            latest_price = self.db.query(StockPrice).filter(
                StockPrice.stock_code == stock_code
            ).order_by(desc(StockPrice.trade_date)).first()
            
            if not latest_price:
                return {}
            
            current_price = latest_price.close_price
            pre_close = latest_price.pre_close_price or latest_price.close_price
            price_change = current_price - pre_close
            price_change_percent = (price_change / pre_close) * 100 if pre_close else 0
            
            price_info = {
                "current_price": current_price,
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "volume": latest_price.volume,
                "turnover_rate": latest_price.turnover_rate
            }
            
            # 缓存结果
            self.cache.set(
                cache_key,
                json.dumps(price_info),
                expire=300  # 5分钟缓存
            )
            
            return price_info
            
        except Exception as e:
            logger.error(f"获取当前价格信息失败: {str(e)}")
            return {}
    
    def _aggregate_weekly_data(self, prices: List[StockPrice]) -> List[StockPrice]:
        """聚合周数据"""
        # 简化实现，实际应该按周聚合
        return prices[::5]  # 每5个取一个
    
    def _aggregate_monthly_data(self, prices: List[StockPrice]) -> List[StockPrice]:
        """聚合月数据"""
        # 简化实现，实际应该按月聚合
        return prices[::20]  # 每20个取一个
    
    def _calculate_technical_indicators(
        self,
        prices: List[StockPrice],
        period: int
    ) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            if len(prices) < period:
                raise ValueError("数据不足")
            
            # 获取收盘价列表
            close_prices = [p.close_price for p in prices[:period]]
            volumes = [p.volume for p in prices[:period]]
            
            # 计算移动平均线
            ma5 = sum(close_prices[:5]) / 5 if len(close_prices) >= 5 else None
            ma10 = sum(close_prices[:10]) / 10 if len(close_prices) >= 10 else None
            ma20 = sum(close_prices[:20]) / 20 if len(close_prices) >= 20 else None
            
            # 计算RSI
            rsi = self._calculate_rsi(close_prices)
            
            # 计算MACD
            macd_data = self._calculate_macd(close_prices)
            
            # 计算布林带
            bollinger_data = self._calculate_bollinger_bands(close_prices, period)
            
            return {
                "ma5": round(ma5, 2) if ma5 else None,
                "ma10": round(ma10, 2) if ma10 else None,
                "ma20": round(ma20, 2) if ma20 else None,
                "rsi": round(rsi, 2) if rsi else None,
                "macd": macd_data,
                "bollinger": bollinger_data,
                "volume_ma": round(sum(volumes) / len(volumes), 0) if volumes else None
            }
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {}
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """计算RSI"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Dict[str, Optional[float]]:
        """计算MACD"""
        if len(prices) < 26:
            return {"macd": None, "signal": None, "histogram": None}
        
        # 简化MACD计算
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        
        if ema12 is None or ema26 is None:
            return {"macd": None, "signal": None, "histogram": None}
        
        macd_line = ema12 - ema26
        
        return {
            "macd": round(macd_line, 4),
            "signal": None,  # 需要更复杂的计算
            "histogram": None
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """计算指数移动平均"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:period]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20
    ) -> Dict[str, Optional[float]]:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        
        # 计算中轨(移动平均)
        middle = sum(prices[:period]) / period
        
        # 计算标准差
        variance = sum((p - middle) ** 2 for p in prices[:period]) / period
        std_dev = variance ** 0.5
        
        # 计算上下轨
        upper = middle + (2 * std_dev)
        lower = middle - (2 * std_dev)
        
        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2)
        }
    
    async def _convert_to_stock_responses(
        self,
        price_data: List[Tuple]
    ) -> List[StockResponse]:
        """转换为股票响应格式"""
        responses = []
        
        for data in price_data:
            stock_code = data[0]
            close_price = data[1]
            pre_close = data[2] if len(data) > 2 else close_price
            volume = data[3] if len(data) > 3 else 0
            
            # 获取股票基本信息
            stock = self.db.query(Stock).filter(Stock.code == stock_code).first()
            
            if not stock:
                continue
            
            price_change = close_price - pre_close
            price_change_percent = (price_change / pre_close) * 100 if pre_close else 0
            
            response = StockResponse(
                code=stock.code,
                name=stock.name,
                industry=stock.industry,
                market=stock.market,
                list_date=stock.list_date,
                market_cap=stock.market_cap,
                pe_ratio=stock.pe_ratio,
                pb_ratio=stock.pb_ratio,
                current_price=close_price,
                price_change=round(price_change, 2),
                price_change_percent=round(price_change_percent, 2),
                volume=volume,
                turnover_rate=None
            )
            responses.append(response)
        
        return responses