from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

from app.models.stock import (
    Recommendation, Stock, StockPrice, StrategyResult,
    RecommendationResponse, RecommendationWithStock,
    RecommendationType
)
from config.database import cache_manager
from config.settings import settings
from loguru import logger


class RecommendationService:
    """推荐服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_manager
    
    async def get_active_recommendations(
        self,
        recommendation_type: RecommendationType,
        limit: int = 10,
        min_confidence: float = 0.6,
        strategy_name: Optional[str] = None
    ) -> List[RecommendationWithStock]:
        """获取活跃推荐"""
        try:
            # 构建查询
            query = self.db.query(Recommendation, Stock).join(
                Stock, Recommendation.stock_code == Stock.code
            ).filter(
                and_(
                    Recommendation.recommendation_type == recommendation_type,
                    Recommendation.is_active == True,
                    Recommendation.confidence_score >= min_confidence,
                    or_(
                        Recommendation.expires_at.is_(None),
                        Recommendation.expires_at > datetime.now()
                    )
                )
            )
            
            # 策略筛选
            if strategy_name:
                query = query.filter(Recommendation.strategy_name == strategy_name)
            
            # 排序和限制
            query = query.order_by(
                desc(Recommendation.confidence_score),
                desc(Recommendation.created_at)
            ).limit(limit)
            
            results = query.all()
            
            # 转换为响应模型
            recommendations = []
            for rec, stock in results:
                # 获取当前价格信息
                current_price_info = await self._get_current_price_info(stock.code)
                
                rec_data = RecommendationWithStock(
                    id=rec.id,
                    stock_code=rec.stock_code,
                    stock_name=stock.name,
                    recommendation_type=rec.recommendation_type,
                    strategy_name=rec.strategy_name,
                    confidence_score=rec.confidence_score,
                    target_price=rec.target_price,
                    stop_loss_price=rec.stop_loss_price,
                    reason=rec.reason,
                    created_at=rec.created_at,
                    expires_at=rec.expires_at,
                    is_active=rec.is_active,
                    current_price=current_price_info.get('current_price'),
                    price_change=current_price_info.get('price_change'),
                    price_change_percent=current_price_info.get('price_change_percent')
                )
                recommendations.append(rec_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取活跃推荐失败: {str(e)}")
            raise
    
    async def get_recommendations_by_date(
        self,
        date: date,
        recommendation_type: Optional[RecommendationType] = None,
        strategy_name: Optional[str] = None
    ) -> List[RecommendationWithStock]:
        """按日期获取推荐"""
        try:
            # 构建查询
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            
            query = self.db.query(Recommendation, Stock).join(
                Stock, Recommendation.stock_code == Stock.code
            ).filter(
                and_(
                    Recommendation.created_at >= start_datetime,
                    Recommendation.created_at <= end_datetime
                )
            )
            
            # 类型筛选
            if recommendation_type:
                query = query.filter(Recommendation.recommendation_type == recommendation_type)
            
            # 策略筛选
            if strategy_name:
                query = query.filter(Recommendation.strategy_name == strategy_name)
            
            # 排序
            query = query.order_by(
                desc(Recommendation.confidence_score),
                desc(Recommendation.created_at)
            )
            
            results = query.all()
            
            # 转换为响应模型
            recommendations = []
            for rec, stock in results:
                current_price_info = await self._get_current_price_info(stock.code)
                
                rec_data = RecommendationWithStock(
                    id=rec.id,
                    stock_code=rec.stock_code,
                    stock_name=stock.name,
                    recommendation_type=rec.recommendation_type,
                    strategy_name=rec.strategy_name,
                    confidence_score=rec.confidence_score,
                    target_price=rec.target_price,
                    stop_loss_price=rec.stop_loss_price,
                    reason=rec.reason,
                    created_at=rec.created_at,
                    expires_at=rec.expires_at,
                    is_active=rec.is_active,
                    current_price=current_price_info.get('current_price'),
                    price_change=current_price_info.get('price_change'),
                    price_change_percent=current_price_info.get('price_change_percent')
                )
                recommendations.append(rec_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"按日期获取推荐失败: {str(e)}")
            raise
    
    async def get_historical_recommendations(
        self,
        date_from: datetime,
        date_to: datetime,
        recommendation_type: Optional[RecommendationType] = None,
        strategy_name: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> List[RecommendationWithStock]:
        """获取历史推荐"""
        try:
            # 构建查询
            query = self.db.query(Recommendation, Stock).join(
                Stock, Recommendation.stock_code == Stock.code
            ).filter(
                and_(
                    Recommendation.created_at >= date_from,
                    Recommendation.created_at <= date_to
                )
            )
            
            # 类型筛选
            if recommendation_type:
                query = query.filter(Recommendation.recommendation_type == recommendation_type)
            
            # 策略筛选
            if strategy_name:
                query = query.filter(Recommendation.strategy_name == strategy_name)
            
            # 分页
            offset = (page - 1) * size
            query = query.order_by(
                desc(Recommendation.created_at)
            ).offset(offset).limit(size)
            
            results = query.all()
            
            # 转换为响应模型
            recommendations = []
            for rec, stock in results:
                current_price_info = await self._get_current_price_info(stock.code)
                
                rec_data = RecommendationWithStock(
                    id=rec.id,
                    stock_code=rec.stock_code,
                    stock_name=stock.name,
                    recommendation_type=rec.recommendation_type,
                    strategy_name=rec.strategy_name,
                    confidence_score=rec.confidence_score,
                    target_price=rec.target_price,
                    stop_loss_price=rec.stop_loss_price,
                    reason=rec.reason,
                    created_at=rec.created_at,
                    expires_at=rec.expires_at,
                    is_active=rec.is_active,
                    current_price=current_price_info.get('current_price'),
                    price_change=current_price_info.get('price_change'),
                    price_change_percent=current_price_info.get('price_change_percent')
                )
                recommendations.append(rec_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取历史推荐失败: {str(e)}")
            raise
    
    async def get_historical_recommendations_paginated(
        self,
        date_from: datetime,
        date_to: datetime,
        recommendation_type: Optional[RecommendationType] = None,
        strategy_name: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> dict:
        """获取历史推荐（带分页信息）"""
        try:
            # 构建基础查询
            base_query = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.created_at >= date_from,
                    Recommendation.created_at <= date_to
                )
            )
            
            # 类型筛选
            if recommendation_type:
                base_query = base_query.filter(Recommendation.recommendation_type == recommendation_type)
            
            # 策略筛选
            if strategy_name:
                base_query = base_query.filter(Recommendation.strategy_name == strategy_name)
            
            # 获取总数
            total = base_query.count()
            
            # 分页查询
            offset = (page - 1) * size
            query = self.db.query(Recommendation, Stock).join(
                Stock, Recommendation.stock_code == Stock.code
            ).filter(
                and_(
                    Recommendation.created_at >= date_from,
                    Recommendation.created_at <= date_to
                )
            )
            
            # 应用相同的筛选条件
            if recommendation_type:
                query = query.filter(Recommendation.recommendation_type == recommendation_type)
            
            if strategy_name:
                query = query.filter(Recommendation.strategy_name == strategy_name)
            
            query = query.order_by(
                desc(Recommendation.created_at)
            ).offset(offset).limit(size)
            
            results = query.all()
            
            # 转换为响应模型
            recommendations = []
            for rec, stock in results:
                current_price_info = await self._get_current_price_info(stock.code)
                
                rec_data = RecommendationWithStock(
                    id=rec.id,
                    stock_code=rec.stock_code,
                    stock_name=stock.name,
                    recommendation_type=rec.recommendation_type,
                    strategy_name=rec.strategy_name,
                    confidence_score=rec.confidence_score,
                    target_price=rec.target_price,
                    stop_loss_price=rec.stop_loss_price,
                    reason=rec.reason,
                    created_at=rec.created_at,
                    expires_at=rec.expires_at,
                    is_active=rec.is_active,
                    current_price=current_price_info.get('current_price'),
                    price_change=current_price_info.get('price_change'),
                    price_change_percent=current_price_info.get('price_change_percent')
                )
                recommendations.append(rec_data)
            
            # 计算总页数
            pages = (total + size - 1) // size
            
            return {
                'items': recommendations,
                'total': total,
                'page': page,
                'size': size,
                'pages': pages
            }
            
        except Exception as e:
            logger.error(f"获取分页历史推荐失败: {str(e)}")
            raise
    
    async def get_stock_recommendations(
        self,
        stock_code: str,
        date_from: datetime,
        date_to: Optional[datetime] = None
    ) -> List[RecommendationResponse]:
        """获取特定股票的推荐历史"""
        try:
            if not date_to:
                date_to = datetime.now()
            
            query = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.stock_code == stock_code,
                    Recommendation.created_at >= date_from,
                    Recommendation.created_at <= date_to
                )
            ).order_by(desc(Recommendation.created_at))
            
            results = query.all()
            
            return [RecommendationResponse.from_orm(rec) for rec in results]
            
        except Exception as e:
            logger.error(f"获取股票推荐历史失败: {str(e)}")
            raise
    
    async def get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        try:
            # 从数据库获取已使用的策略
            strategies = self.db.query(
                Recommendation.strategy_name
            ).distinct().all()
            
            strategy_list = [s[0] for s in strategies]
            
            # 添加配置中的策略
            from config.settings import STRATEGY_CONFIG
            for category, strategies_config in STRATEGY_CONFIG.items():
                for strategy_name in strategies_config.keys():
                    full_name = f"{category}.{strategy_name}"
                    if full_name not in strategy_list:
                        strategy_list.append(full_name)
            
            return sorted(strategy_list)
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {str(e)}")
            raise
    
    async def get_strategy_performance(
        self,
        strategy_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取策略表现统计"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取策略推荐
            recommendations = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.strategy_name == strategy_name,
                    Recommendation.created_at >= start_date,
                    Recommendation.created_at <= end_date
                )
            ).all()
            
            # 统计数据
            total_recommendations = len(recommendations)
            buy_recommendations = len([r for r in recommendations if r.recommendation_type == RecommendationType.BUY])
            sell_recommendations = len([r for r in recommendations if r.recommendation_type == RecommendationType.SELL])
            
            # 计算平均置信度
            avg_confidence = sum(r.confidence_score for r in recommendations) / total_recommendations if total_recommendations > 0 else 0
            
            # 计算成功率(这里需要根据实际价格变化来计算)
            success_rate = await self._calculate_success_rate(recommendations)
            
            return {
                "strategy_name": strategy_name,
                "period_days": days,
                "total_recommendations": total_recommendations,
                "buy_recommendations": buy_recommendations,
                "sell_recommendations": sell_recommendations,
                "average_confidence": round(avg_confidence, 3),
                "success_rate": round(success_rate, 3),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取策略表现失败: {str(e)}")
            raise
    
    async def refresh_recommendations(
        self,
        strategy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """刷新推荐(触发策略执行)"""
        try:
            # 这里应该调用策略执行服务
            # 暂时返回模拟结果
            result = {
                "refreshed_at": datetime.now().isoformat(),
                "strategy": strategy_name or "all",
                "status": "success",
                "message": "推荐刷新完成"
            }
            
            logger.info(f"推荐刷新完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"推荐刷新失败: {str(e)}")
            raise
    
    async def get_recommendations_summary(self) -> Dict[str, Any]:
        """获取推荐汇总信息"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            
            # 今日推荐统计
            today_recommendations = self.db.query(Recommendation).filter(
                Recommendation.created_at >= start_of_day
            ).all()
            
            today_buy = len([r for r in today_recommendations if r.recommendation_type == RecommendationType.BUY])
            today_sell = len([r for r in today_recommendations if r.recommendation_type == RecommendationType.SELL])
            
            # 活跃推荐统计
            active_recommendations = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.is_active == True,
                    or_(
                        Recommendation.expires_at.is_(None),
                        Recommendation.expires_at > datetime.now()
                    )
                )
            ).all()
            
            active_buy = len([r for r in active_recommendations if r.recommendation_type == RecommendationType.BUY])
            active_sell = len([r for r in active_recommendations if r.recommendation_type == RecommendationType.SELL])
            
            # 策略统计
            strategy_stats = self.db.query(
                Recommendation.strategy_name,
                func.count(Recommendation.id).label('count')
            ).filter(
                Recommendation.created_at >= start_of_day
            ).group_by(Recommendation.strategy_name).all()
            
            return {
                "today": {
                    "total": len(today_recommendations),
                    "buy": today_buy,
                    "sell": today_sell
                },
                "active": {
                    "total": len(active_recommendations),
                    "buy": active_buy,
                    "sell": active_sell
                },
                "strategies": {
                    strategy: count for strategy, count in strategy_stats
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取推荐汇总失败: {str(e)}")
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
            
            # 获取前一日价格计算涨跌
            prev_price = self.db.query(StockPrice).filter(
                and_(
                    StockPrice.stock_code == stock_code,
                    StockPrice.trade_date < latest_price.trade_date
                )
            ).order_by(desc(StockPrice.trade_date)).first()
            
            current_price = latest_price.close_price
            price_change = 0
            price_change_percent = 0
            
            if prev_price and prev_price.close_price:
                price_change = current_price - prev_price.close_price
                price_change_percent = (price_change / prev_price.close_price) * 100
            
            price_info = {
                "current_price": current_price,
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2)
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
    
    async def _calculate_success_rate(self, recommendations: List[Recommendation]) -> float:
        """计算推荐成功率"""
        try:
            if not recommendations:
                return 0.0
            
            successful_count = 0
            
            for rec in recommendations:
                # 获取推荐后的价格变化
                future_prices = self.db.query(StockPrice).filter(
                    and_(
                        StockPrice.stock_code == rec.stock_code,
                        StockPrice.trade_date > rec.created_at
                    )
                ).order_by(StockPrice.trade_date).limit(5).all()
                
                if not future_prices:
                    continue
                
                # 获取推荐时的价格
                rec_date_price = self.db.query(StockPrice).filter(
                    and_(
                        StockPrice.stock_code == rec.stock_code,
                        StockPrice.trade_date <= rec.created_at
                    )
                ).order_by(desc(StockPrice.trade_date)).first()
                
                if not rec_date_price:
                    continue
                
                # 判断推荐是否成功
                if rec.recommendation_type == RecommendationType.BUY:
                    # 买入推荐：后续价格上涨则成功
                    max_price = max(p.close_price for p in future_prices)
                    if max_price > rec_date_price.close_price * 1.02:  # 上涨2%以上
                        successful_count += 1
                elif rec.recommendation_type == RecommendationType.SELL:
                    # 卖出推荐：后续价格下跌则成功
                    min_price = min(p.close_price for p in future_prices)
                    if min_price < rec_date_price.close_price * 0.98:  # 下跌2%以上
                        successful_count += 1
            
            return successful_count / len(recommendations)
            
        except Exception as e:
            logger.error(f"计算成功率失败: {str(e)}")
            return 0.0