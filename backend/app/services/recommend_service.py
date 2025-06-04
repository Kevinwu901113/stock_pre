#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐服务模块
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import Depends

from ..core.config import settings
from ..core.logging import get_logger
from ..models.recommendation import (
    Recommendation, RecommendationType, RecommendationLevel,
    RecommendationStatus, RecommendationPerformance,
    RecommendationExplanation
)
from .data_service import DataService
from .strategy_service import StrategyService

logger = get_logger(__name__)


class RecommendService:
    """推荐服务类"""
    
    def __init__(self, data_service: DataService = Depends(DataService)):
        """初始化推荐服务"""
        self.data_service = data_service
        self.recommendations_cache = {}
        
        logger.info("推荐服务初始化完成")
    
    async def get_recommendations(
        self,
        recommendation_type: str,
        target_date: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取推荐列表"""
        try:
            logger.info(f"获取推荐列表: 类型={recommendation_type}, 日期={target_date}")
            
            # 设置默认日期
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            # 根据推荐类型调用相应方法
            if recommendation_type == "buy":
                return await self.get_evening_buy_recommendations(target_date, limit)
            elif recommendation_type == "sell":
                return await self.get_morning_sell_recommendations(target_date, limit)
            else:
                raise ValueError(f"不支持的推荐类型: {recommendation_type}")
                
        except Exception as e:
            logger.error(f"获取推荐列表失败: {str(e)}")
            raise
    
    async def get_evening_buy_recommendations(
        self,
        target_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取尾盘买入推荐"""
        try:
            logger.info(f"获取尾盘买入推荐: 日期={target_date}")
            
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            # 检查缓存
            cache_key = f"evening_buy_{target_date}_{limit}"
            if cache_key in self.recommendations_cache:
                logger.info(f"使用缓存推荐: {cache_key}")
                return self.recommendations_cache[cache_key]
            
            # 生成尾盘买入推荐
            recommendations = await self._generate_evening_buy_recommendations(target_date, limit)
            
            # 缓存结果
            self.recommendations_cache[cache_key] = recommendations
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取尾盘买入推荐失败: {str(e)}")
            raise
    
    async def get_morning_sell_recommendations(
        self,
        target_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取早盘卖出推荐"""
        try:
            logger.info(f"获取早盘卖出推荐: 日期={target_date}")
            
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            # 检查缓存
            cache_key = f"morning_sell_{target_date}_{limit}"
            if cache_key in self.recommendations_cache:
                logger.info(f"使用缓存推荐: {cache_key}")
                return self.recommendations_cache[cache_key]
            
            # 生成早盘卖出推荐
            recommendations = await self._generate_morning_sell_recommendations(target_date, limit)
            
            # 缓存结果
            self.recommendations_cache[cache_key] = recommendations
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取早盘卖出推荐失败: {str(e)}")
            raise
    
    async def _generate_evening_buy_recommendations(
        self,
        target_date: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """生成尾盘买入推荐"""
        try:
            logger.info(f"生成尾盘买入推荐: {target_date}")
            
            # 获取股票池
            stock_pool = await self._get_stock_pool()
            
            recommendations = []
            
            # 遍历股票池，应用尾盘买入策略
            for stock_code in stock_pool[:limit * 2]:  # 获取更多候选股票
                try:
                    # 获取股票数据
                    end_date = target_date
                    start_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
                    stock_data = await self.data_service.get_stock_data(stock_code, start_date, end_date)
                    
                    if stock_data.empty:
                        continue
                    
                    # 应用尾盘买入策略
                    signal = await self._apply_evening_buy_strategy(stock_data)
                    
                    if signal['buy_signal']:
                        # 获取股票信息
                        stock_info = await self.data_service.get_stock_info(stock_code)
                        
                        recommendation = {
                            "stock_code": stock_code,
                            "stock_name": stock_info.get("name", f"股票{stock_code}"),
                            "recommendation_type": "buy",
                            "recommendation_level": self._determine_recommendation_level(signal['confidence']),
                            "strategy_name": "尾盘5分钟均线突破买入",
                            "current_price": float(stock_data.iloc[-1]['close_price']),
                            "target_price": signal.get('target_price'),
                            "stop_loss_price": signal.get('stop_loss_price'),
                            "confidence_score": signal['confidence'],
                            "expected_return": signal.get('expected_return', 5.0),
                            "risk_level": signal.get('risk_level', 3),
                            "recommendation_date": target_date,
                            "reason": signal['reason'],
                            "technical_signals": signal.get('technical_signals', {}),
                            "status": "active"
                        }
                        
                        recommendations.append(recommendation)
                        
                        if len(recommendations) >= limit:
                            break
                            
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 时出错: {str(e)}")
                    continue
            
            # 按置信度排序
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            logger.info(f"生成了 {len(recommendations)} 个尾盘买入推荐")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"生成尾盘买入推荐失败: {str(e)}")
            raise
    
    async def _generate_morning_sell_recommendations(
        self,
        target_date: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """生成早盘卖出推荐"""
        try:
            logger.info(f"生成早盘卖出推荐: {target_date}")
            
            # 获取持仓股票（这里模拟一些持仓股票）
            holding_stocks = await self._get_holding_stocks()
            
            recommendations = []
            
            # 遍历持仓股票，应用早盘卖出策略
            for stock_code in holding_stocks:
                try:
                    # 获取股票数据
                    end_date = target_date
                    start_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
                    stock_data = await self.data_service.get_stock_data(stock_code, start_date, end_date)
                    
                    if stock_data.empty:
                        continue
                    
                    # 应用早盘卖出策略
                    signal = await self._apply_morning_sell_strategy(stock_data)
                    
                    if signal['sell_signal']:
                        # 获取股票信息
                        stock_info = await self.data_service.get_stock_info(stock_code)
                        
                        recommendation = {
                            "stock_code": stock_code,
                            "stock_name": stock_info.get("name", f"股票{stock_code}"),
                            "recommendation_type": "sell",
                            "recommendation_level": self._determine_recommendation_level(signal['confidence']),
                            "strategy_name": "早盘高开高走止盈",
                            "current_price": float(stock_data.iloc[-1]['close_price']),
                            "target_price": signal.get('target_price'),
                            "confidence_score": signal['confidence'],
                            "expected_return": signal.get('expected_return', 3.0),
                            "risk_level": signal.get('risk_level', 2),
                            "recommendation_date": target_date,
                            "reason": signal['reason'],
                            "technical_signals": signal.get('technical_signals', {}),
                            "status": "active"
                        }
                        
                        recommendations.append(recommendation)
                        
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 时出错: {str(e)}")
                    continue
            
            # 按置信度排序
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            logger.info(f"生成了 {len(recommendations)} 个早盘卖出推荐")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"生成早盘卖出推荐失败: {str(e)}")
            raise
    
    async def _apply_evening_buy_strategy(self, stock_data: pd.DataFrame) -> Dict[str, Any]:
        """应用尾盘买入策略"""
        try:
            # 获取最新数据
            latest = stock_data.iloc[-1]
            recent_data = stock_data.tail(10)
            
            # 计算5日均线
            ma5 = recent_data['close_price'].rolling(window=5).mean().iloc[-1]
            
            # 计算成交量比率
            avg_volume = recent_data['volume'].mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            
            # 计算涨跌幅
            pct_change = latest.get('pct_change', 0)
            
            # 策略逻辑
            buy_signal = False
            confidence = 0
            reason = ""
            
            # 条件1: 价格突破5日均线
            if latest['close_price'] > ma5:
                confidence += 30
                reason += "价格突破5日均线; "
            
            # 条件2: 成交量放大
            if volume_ratio > 1.5:
                confidence += 25
                reason += f"成交量放大{volume_ratio:.1f}倍; "
            
            # 条件3: 涨幅适中
            if 0 < pct_change < 5:
                confidence += 20
                reason += f"涨幅适中({pct_change:.1f}%); "
            
            # 条件4: 价格在合理区间
            if 5 < latest['close_price'] < 100:
                confidence += 15
                reason += "价格在合理区间; "
            
            # 条件5: 近期表现
            recent_performance = recent_data['pct_change'].mean()
            if recent_performance > -2:
                confidence += 10
                reason += "近期表现良好; "
            
            # 判断买入信号
            if confidence >= 60:
                buy_signal = True
            
            # 计算目标价和止损价
            target_price = latest['close_price'] * 1.05  # 5%目标收益
            stop_loss_price = latest['close_price'] * 0.97  # 3%止损
            
            return {
                'buy_signal': buy_signal,
                'confidence': confidence,
                'reason': reason.strip('; '),
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'expected_return': 5.0,
                'risk_level': 3,
                'technical_signals': {
                    'ma5': ma5,
                    'volume_ratio': volume_ratio,
                    'pct_change': pct_change,
                    'recent_performance': recent_performance
                }
            }
            
        except Exception as e:
            logger.error(f"应用尾盘买入策略失败: {str(e)}")
            raise
    
    async def _apply_morning_sell_strategy(self, stock_data: pd.DataFrame) -> Dict[str, Any]:
        """应用早盘卖出策略"""
        try:
            # 获取最新数据
            latest = stock_data.iloc[-1]
            recent_data = stock_data.tail(5)
            
            # 计算涨跌幅
            pct_change = latest.get('pct_change', 0)
            
            # 计算近期累计涨幅
            cumulative_return = (recent_data['close_price'].iloc[-1] / recent_data['close_price'].iloc[0] - 1) * 100
            
            # 策略逻辑
            sell_signal = False
            confidence = 0
            reason = ""
            
            # 条件1: 高开高走
            if latest['open_price'] > recent_data['close_price'].iloc[-2] and latest['close_price'] > latest['open_price']:
                confidence += 35
                reason += "高开高走形态; "
            
            # 条件2: 涨幅较大
            if pct_change > 3:
                confidence += 30
                reason += f"当日涨幅较大({pct_change:.1f}%); "
            
            # 条件3: 累计涨幅
            if cumulative_return > 10:
                confidence += 25
                reason += f"近期累计涨幅较大({cumulative_return:.1f}%); "
            
            # 条件4: 成交量
            avg_volume = recent_data['volume'].mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            if volume_ratio > 2:
                confidence += 10
                reason += "成交量异常放大; "
            
            # 判断卖出信号
            if confidence >= 70:
                sell_signal = True
            
            # 计算目标价
            target_price = latest['close_price'] * 1.03  # 3%目标收益
            
            return {
                'sell_signal': sell_signal,
                'confidence': confidence,
                'reason': reason.strip('; '),
                'target_price': target_price,
                'expected_return': 3.0,
                'risk_level': 2,
                'technical_signals': {
                    'pct_change': pct_change,
                    'cumulative_return': cumulative_return,
                    'volume_ratio': volume_ratio,
                    'high_open': latest['open_price'] > recent_data['close_price'].iloc[-2]
                }
            }
            
        except Exception as e:
            logger.error(f"应用早盘卖出策略失败: {str(e)}")
            raise
    
    def _determine_recommendation_level(self, confidence: float) -> str:
        """根据置信度确定推荐等级"""
        if confidence >= 90:
            return "strong_buy"
        elif confidence >= 80:
            return "buy"
        elif confidence >= 70:
            return "weak_buy"
        elif confidence >= 60:
            return "hold"
        elif confidence >= 50:
            return "weak_sell"
        elif confidence >= 40:
            return "sell"
        else:
            return "strong_sell"
    
    async def _get_stock_pool(self) -> List[str]:
        """获取股票池"""
        # 这里返回一些模拟的股票代码
        return [
            "600000", "600001", "600002", "600003", "600004",
            "600005", "600006", "600007", "600008", "600009",
            "000001", "000002", "000003", "000004", "000005",
            "300001", "300002", "300003", "300004", "300005"
        ]
    
    async def _get_holding_stocks(self) -> List[str]:
        """获取持仓股票"""
        # 这里返回一些模拟的持仓股票代码
        return [
            "600000", "600001", "000001", "000002", "300001"
        ]
    
    async def get_recommendation_history(
        self,
        start_date: str,
        end_date: str,
        recommendation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取历史推荐记录"""
        try:
            logger.info(f"获取历史推荐: {start_date} 到 {end_date}")
            
            # TODO: 实现实际的历史推荐查询逻辑
            # 这里返回模拟数据
            history = []
            
            return history
            
        except Exception as e:
            logger.error(f"获取历史推荐失败: {str(e)}")
            raise
    
    async def get_recommendation_performance(
        self,
        start_date: str,
        end_date: str,
        recommendation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取推荐策略表现统计"""
        try:
            logger.info(f"获取推荐表现: {start_date} 到 {end_date}")
            
            # TODO: 实现实际的表现统计逻辑
            # 这里返回模拟数据
            performance = {
                "total_recommendations": 100,
                "successful_recommendations": 65,
                "success_rate": 65.0,
                "average_return": 3.2,
                "max_return": 15.8,
                "min_return": -8.5,
                "total_return": 12.5,
                "win_rate": 68.0,
                "start_date": start_date,
                "end_date": end_date
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"获取推荐表现失败: {str(e)}")
            raise
    
    async def generate_recommendations(
        self,
        recommendation_type: str,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """手动生成推荐"""
        try:
            logger.info(f"手动生成推荐: 类型={recommendation_type}")
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 清除缓存（如果强制重新生成）
            if force_regenerate:
                cache_keys_to_remove = [k for k in self.recommendations_cache.keys() if recommendation_type in k]
                for key in cache_keys_to_remove:
                    del self.recommendations_cache[key]
            
            # 生成推荐
            if recommendation_type == "buy":
                recommendations = await self.get_evening_buy_recommendations(today, 20)
            elif recommendation_type == "sell":
                recommendations = await self.get_morning_sell_recommendations(today, 20)
            else:
                raise ValueError(f"不支持的推荐类型: {recommendation_type}")
            
            return {
                "count": len(recommendations),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"生成推荐失败: {str(e)}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取推荐系统状态"""
        try:
            status = {
                "service_status": "running",
                "cache_count": len(self.recommendations_cache),
                "last_update": datetime.now().isoformat(),
                "available_strategies": [
                    "尾盘5分钟均线突破买入",
                    "早盘高开高走止盈"
                ]
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            raise
    
    async def explain_recommendation(
        self,
        stock_code: str,
        recommendation_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """解释推荐理由"""
        try:
            logger.info(f"解释推荐理由: {stock_code}")
            
            if not recommendation_date:
                recommendation_date = datetime.now().strftime("%Y-%m-%d")
            
            # TODO: 实现实际的推荐解释逻辑
            # 这里返回模拟数据
            explanation = {
                "stock_code": stock_code,
                "stock_name": f"股票{stock_code}",
                "recommendation_type": "buy",
                "strategy_name": "尾盘5分钟均线突破买入",
                "main_reason": "该股票符合尾盘突破买入条件",
                "technical_analysis": {
                    "ma5_breakthrough": True,
                    "volume_amplification": 1.8,
                    "price_trend": "上升",
                    "support_level": 15.2
                },
                "risk_factors": [
                    "市场整体波动风险",
                    "个股基本面变化风险"
                ],
                "key_indicators": {
                    "confidence_score": 75.0,
                    "expected_return": 5.0,
                    "risk_level": 3
                },
                "confidence_breakdown": {
                    "技术指标": 30.0,
                    "成交量": 25.0,
                    "价格趋势": 20.0
                }
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"解释推荐理由失败: {str(e)}")
            raise