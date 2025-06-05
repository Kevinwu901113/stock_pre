from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base import BaseStrategy
from loguru import logger


class ValueInvestmentStrategy(BaseStrategy):
    """价值投资策略
    
    基于基本面指标寻找被低估的股票。
    主要关注PE、PB、ROE等指标。
    """
    
    def get_description(self) -> str:
        return "基于基本面指标的价值投资策略，寻找PE、PB较低但ROE较高的优质股票"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'max_pe_ratio': {
                'type': float,
                'default': 20.0,
                'min': 5.0,
                'max': 50.0,
                'description': '最大市盈率'
            },
            'max_pb_ratio': {
                'type': float,
                'default': 3.0,
                'min': 0.5,
                'max': 10.0,
                'description': '最大市净率'
            },
            'min_roe': {
                'type': float,
                'default': 0.10,
                'min': 0.05,
                'max': 0.30,
                'description': '最小净资产收益率'
            },
            'min_market_cap': {
                'type': float,
                'default': 50.0,
                'min': 10.0,
                'max': 1000.0,
                'description': '最小市值(亿元)'
            },
            'debt_ratio_threshold': {
                'type': float,
                'default': 0.6,
                'min': 0.3,
                'max': 0.8,
                'description': '资产负债率阈值'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        max_pe = self.get_parameter('max_pe_ratio', 20.0)
        max_pb = self.get_parameter('max_pb_ratio', 3.0)
        min_roe = self.get_parameter('min_roe', 0.10)
        min_market_cap = self.get_parameter('min_market_cap', 50.0)
        debt_threshold = self.get_parameter('debt_ratio_threshold', 0.6)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取股票基本信息
                stock_info = await self.get_stock_info(stock_code)
                if not stock_info:
                    continue
                
                # 获取基本面数据
                fundamental_data = await self.get_fundamental_data(stock_code)
                if not fundamental_data:
                    continue
                
                # 提取关键指标
                pe_ratio = stock_info.get('pe_ratio', 0)
                pb_ratio = stock_info.get('pb_ratio', 0)
                market_cap = stock_info.get('market_cap', 0)
                roe = fundamental_data.get('roe', 0)
                debt_ratio = fundamental_data.get('debt_ratio', 1.0)
                revenue_growth = fundamental_data.get('revenue_growth', 0)
                profit_growth = fundamental_data.get('profit_growth', 0)
                
                # 跳过数据不完整的股票
                if pe_ratio <= 0 or pb_ratio <= 0 or market_cap <= 0:
                    continue
                
                # 基本筛选条件
                if (pe_ratio > max_pe or 
                    pb_ratio > max_pb or 
                    roe < min_roe or 
                    market_cap < min_market_cap or 
                    debt_ratio > debt_threshold):
                    continue
                
                # 计算价值评分
                value_score = self.calculate_value_score(
                    pe_ratio, pb_ratio, roe, revenue_growth, profit_growth, debt_ratio
                )
                
                if value_score >= 0.6:  # 只推荐高分股票
                    # 获取价格数据用于技术面确认
                    price_data = await self.get_stock_data(stock_code, days=30)
                    if not price_data:
                        continue
                    
                    close_prices = [p['close'] for p in price_data]
                    current_price = close_prices[0]
                    
                    # 技术面确认(可选)
                    tech_confirmation = self.get_technical_confirmation(close_prices)
                    
                    confidence = value_score
                    if tech_confirmation['trend'] == 'up':
                        confidence += 0.1
                    
                    # 构建推荐理由
                    reason = self.build_value_reason(
                        pe_ratio, pb_ratio, roe, revenue_growth, 
                        profit_growth, debt_ratio, value_score
                    )
                    
                    # 计算目标价格(基于PB和ROE)
                    book_value_per_share = current_price / pb_ratio
                    target_pb = min(pb_ratio * 1.3, max_pb * 0.8)  # 适度估值修复
                    target_price = book_value_per_share * target_pb
                    
                    expected_return = (target_price - current_price) / current_price
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal='buy',
                        confidence=min(confidence, 1.0),
                        reason=reason,
                        target_price=target_price,
                        stop_loss=current_price * 0.85,  # 15%止损
                        expected_return=expected_return,
                        holding_period="3-12个月",
                        additional_data={
                            'pe_ratio': pe_ratio,
                            'pb_ratio': pb_ratio,
                            'roe': roe,
                            'market_cap': market_cap,
                            'debt_ratio': debt_ratio,
                            'value_score': value_score,
                            'revenue_growth': revenue_growth,
                            'profit_growth': profit_growth
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results
    
    async def get_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """获取基本面数据(模拟实现)"""
        # 这里应该从数据库或API获取真实的基本面数据
        # 目前返回模拟数据
        import random
        
        return {
            'roe': random.uniform(0.05, 0.25),
            'debt_ratio': random.uniform(0.2, 0.7),
            'revenue_growth': random.uniform(-0.1, 0.3),
            'profit_growth': random.uniform(-0.2, 0.5),
            'gross_margin': random.uniform(0.1, 0.4),
            'current_ratio': random.uniform(1.0, 3.0)
        }
    
    def calculate_value_score(
        self, 
        pe_ratio: float, 
        pb_ratio: float, 
        roe: float, 
        revenue_growth: float, 
        profit_growth: float, 
        debt_ratio: float
    ) -> float:
        """计算价值评分"""
        score = 0.0
        
        # PE评分 (权重25%)
        if pe_ratio < 10:
            score += 0.25
        elif pe_ratio < 15:
            score += 0.20
        elif pe_ratio < 20:
            score += 0.15
        else:
            score += 0.05
        
        # PB评分 (权重20%)
        if pb_ratio < 1.5:
            score += 0.20
        elif pb_ratio < 2.0:
            score += 0.15
        elif pb_ratio < 3.0:
            score += 0.10
        else:
            score += 0.05
        
        # ROE评分 (权重25%)
        if roe > 0.20:
            score += 0.25
        elif roe > 0.15:
            score += 0.20
        elif roe > 0.10:
            score += 0.15
        else:
            score += 0.05
        
        # 成长性评分 (权重20%)
        avg_growth = (revenue_growth + profit_growth) / 2
        if avg_growth > 0.20:
            score += 0.20
        elif avg_growth > 0.10:
            score += 0.15
        elif avg_growth > 0.05:
            score += 0.10
        else:
            score += 0.05
        
        # 财务健康度评分 (权重10%)
        if debt_ratio < 0.3:
            score += 0.10
        elif debt_ratio < 0.5:
            score += 0.08
        elif debt_ratio < 0.6:
            score += 0.05
        else:
            score += 0.02
        
        return score
    
    def get_technical_confirmation(self, close_prices: List[float]) -> Dict[str, Any]:
        """技术面确认"""
        if len(close_prices) < 20:
            return {'trend': 'neutral', 'strength': 0.5}
        
        # 简单趋势判断
        ma_5 = self.calculate_ma(close_prices, 5)
        ma_20 = self.calculate_ma(close_prices, 20)
        
        if ma_5 and ma_20:
            if ma_5 > ma_20 * 1.02:
                return {'trend': 'up', 'strength': 0.7}
            elif ma_5 < ma_20 * 0.98:
                return {'trend': 'down', 'strength': 0.7}
        
        return {'trend': 'neutral', 'strength': 0.5}
    
    def build_value_reason(
        self, 
        pe_ratio: float, 
        pb_ratio: float, 
        roe: float, 
        revenue_growth: float, 
        profit_growth: float, 
        debt_ratio: float, 
        value_score: float
    ) -> str:
        """构建价值投资推荐理由"""
        reasons = []
        
        if pe_ratio < 15:
            reasons.append(f"PE({pe_ratio:.1f})处于低估值区间")
        
        if pb_ratio < 2.0:
            reasons.append(f"PB({pb_ratio:.1f})低于合理水平")
        
        if roe > 0.15:
            reasons.append(f"ROE({roe:.1%})显示良好盈利能力")
        
        if revenue_growth > 0.1:
            reasons.append(f"营收增长({revenue_growth:.1%})稳健")
        
        if profit_growth > 0.1:
            reasons.append(f"利润增长({profit_growth:.1%})良好")
        
        if debt_ratio < 0.4:
            reasons.append(f"资产负债率({debt_ratio:.1%})较低，财务稳健")
        
        base_reason = "，".join(reasons)
        return f"价值评分{value_score:.2f}，{base_reason}，具备长期投资价值"


class GrowthStrategy(BaseStrategy):
    """成长股策略
    
    寻找高成长性的股票，关注营收增长、利润增长等指标。
    """
    
    def get_description(self) -> str:
        return "成长股投资策略，寻找营收和利润持续高增长的股票"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'min_revenue_growth': {
                'type': float,
                'default': 0.20,
                'min': 0.10,
                'max': 1.0,
                'description': '最小营收增长率'
            },
            'min_profit_growth': {
                'type': float,
                'default': 0.25,
                'min': 0.15,
                'max': 1.0,
                'description': '最小利润增长率'
            },
            'max_pe_ratio': {
                'type': float,
                'default': 40.0,
                'min': 20.0,
                'max': 80.0,
                'description': '最大可接受PE'
            },
            'min_roe': {
                'type': float,
                'default': 0.15,
                'min': 0.10,
                'max': 0.30,
                'description': '最小ROE'
            },
            'growth_consistency': {
                'type': int,
                'default': 3,
                'min': 2,
                'max': 5,
                'description': '成长一致性要求(连续季度)'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        min_revenue_growth = self.get_parameter('min_revenue_growth', 0.20)
        min_profit_growth = self.get_parameter('min_profit_growth', 0.25)
        max_pe = self.get_parameter('max_pe_ratio', 40.0)
        min_roe = self.get_parameter('min_roe', 0.15)
        growth_consistency = self.get_parameter('growth_consistency', 3)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取股票基本信息
                stock_info = await self.get_stock_info(stock_code)
                if not stock_info:
                    continue
                
                # 获取成长性数据
                growth_data = await self.get_growth_data(stock_code)
                if not growth_data:
                    continue
                
                pe_ratio = stock_info.get('pe_ratio', 0)
                roe = growth_data.get('roe', 0)
                revenue_growth = growth_data.get('revenue_growth', 0)
                profit_growth = growth_data.get('profit_growth', 0)
                growth_stability = growth_data.get('growth_stability', 0)
                
                # 基本筛选
                if (pe_ratio <= 0 or pe_ratio > max_pe or
                    roe < min_roe or
                    revenue_growth < min_revenue_growth or
                    profit_growth < min_profit_growth or
                    growth_stability < growth_consistency):
                    continue
                
                # 计算成长评分
                growth_score = self.calculate_growth_score(
                    revenue_growth, profit_growth, roe, growth_stability, pe_ratio
                )
                
                if growth_score >= 0.7:  # 高标准筛选成长股
                    # 获取价格数据
                    price_data = await self.get_stock_data(stock_code, days=60)
                    if not price_data:
                        continue
                    
                    close_prices = [p['close'] for p in price_data]
                    current_price = close_prices[0]
                    
                    # 动量确认
                    momentum = self.calculate_momentum(close_prices)
                    
                    confidence = growth_score
                    if momentum > 0.05:  # 价格动量向上
                        confidence += 0.1
                    
                    # 构建推荐理由
                    reason = self.build_growth_reason(
                        revenue_growth, profit_growth, roe, 
                        growth_stability, pe_ratio, growth_score
                    )
                    
                    # 基于成长性计算目标价格
                    # PEG估值法
                    peg_ratio = pe_ratio / (profit_growth * 100)
                    if peg_ratio < 1.0:  # PEG < 1 表示估值合理
                        target_pe = pe_ratio * 1.2  # 给予一定估值溢价
                        eps = current_price / pe_ratio
                        target_price = eps * target_pe
                    else:
                        target_price = current_price * 1.15  # 保守15%目标
                    
                    expected_return = (target_price - current_price) / current_price
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal='buy',
                        confidence=min(confidence, 1.0),
                        reason=reason,
                        target_price=target_price,
                        stop_loss=current_price * 0.80,  # 20%止损
                        expected_return=expected_return,
                        holding_period="6-18个月",
                        additional_data={
                            'pe_ratio': pe_ratio,
                            'roe': roe,
                            'revenue_growth': revenue_growth,
                            'profit_growth': profit_growth,
                            'growth_score': growth_score,
                            'peg_ratio': peg_ratio,
                            'momentum': momentum
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results
    
    async def get_growth_data(self, stock_code: str) -> Dict[str, Any]:
        """获取成长性数据(模拟实现)"""
        import random
        
        return {
            'roe': random.uniform(0.10, 0.30),
            'revenue_growth': random.uniform(0.15, 0.50),
            'profit_growth': random.uniform(0.20, 0.60),
            'growth_stability': random.randint(2, 5),  # 连续增长季度数
            'market_share_growth': random.uniform(0.05, 0.20)
        }
    
    def calculate_growth_score(
        self, 
        revenue_growth: float, 
        profit_growth: float, 
        roe: float, 
        growth_stability: int, 
        pe_ratio: float
    ) -> float:
        """计算成长评分"""
        score = 0.0
        
        # 营收增长评分 (权重30%)
        if revenue_growth > 0.30:
            score += 0.30
        elif revenue_growth > 0.25:
            score += 0.25
        elif revenue_growth > 0.20:
            score += 0.20
        else:
            score += 0.10
        
        # 利润增长评分 (权重35%)
        if profit_growth > 0.40:
            score += 0.35
        elif profit_growth > 0.30:
            score += 0.30
        elif profit_growth > 0.25:
            score += 0.25
        else:
            score += 0.15
        
        # ROE评分 (权重20%)
        if roe > 0.25:
            score += 0.20
        elif roe > 0.20:
            score += 0.15
        elif roe > 0.15:
            score += 0.10
        else:
            score += 0.05
        
        # 成长稳定性评分 (权重10%)
        if growth_stability >= 4:
            score += 0.10
        elif growth_stability >= 3:
            score += 0.08
        else:
            score += 0.05
        
        # PEG调整 (权重5%)
        peg = pe_ratio / (profit_growth * 100)
        if peg < 0.8:
            score += 0.05
        elif peg < 1.2:
            score += 0.03
        else:
            score += 0.01
        
        return score
    
    def calculate_momentum(self, close_prices: List[float]) -> float:
        """计算价格动量"""
        if len(close_prices) < 20:
            return 0
        
        # 计算20日收益率
        current_price = close_prices[0]
        price_20_days_ago = close_prices[19]
        
        return (current_price - price_20_days_ago) / price_20_days_ago
    
    def build_growth_reason(
        self, 
        revenue_growth: float, 
        profit_growth: float, 
        roe: float, 
        growth_stability: int, 
        pe_ratio: float, 
        growth_score: float
    ) -> str:
        """构建成长股推荐理由"""
        reasons = []
        
        reasons.append(f"营收增长{revenue_growth:.1%}")
        reasons.append(f"利润增长{profit_growth:.1%}")
        
        if roe > 0.20:
            reasons.append(f"ROE({roe:.1%})优秀")
        
        if growth_stability >= 4:
            reasons.append(f"连续{growth_stability}个季度保持增长")
        
        peg = pe_ratio / (profit_growth * 100)
        if peg < 1.0:
            reasons.append(f"PEG({peg:.2f})估值合理")
        
        base_reason = "，".join(reasons)
        return f"成长评分{growth_score:.2f}，{base_reason}，具备高成长投资价值"