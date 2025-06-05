from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base import BaseStrategy
from loguru import logger


class MovingAverageCrossStrategy(BaseStrategy):
    """移动平均线交叉策略
    
    基于短期和长期移动平均线的交叉信号进行买卖判断。
    黄金交叉时买入，死亡交叉时卖出。
    """
    
    def get_description(self) -> str:
        return "基于移动平均线交叉的策略，短期均线上穿长期均线时买入，下穿时卖出"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'short_period': {
                'type': int,
                'default': 5,
                'min': 3,
                'max': 20,
                'description': '短期移动平均线周期'
            },
            'long_period': {
                'type': int,
                'default': 20,
                'min': 10,
                'max': 60,
                'description': '长期移动平均线周期'
            },
            'volume_threshold': {
                'type': float,
                'default': 1.5,
                'min': 1.0,
                'max': 3.0,
                'description': '成交量放大倍数阈值'
            },
            'min_confidence': {
                'type': float,
                'default': 0.6,
                'min': 0.1,
                'max': 1.0,
                'description': '最小置信度阈值'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        short_period = self.get_parameter('short_period', 5)
        long_period = self.get_parameter('long_period', 20)
        volume_threshold = self.get_parameter('volume_threshold', 1.5)
        min_confidence = self.get_parameter('min_confidence', 0.6)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取足够的历史数据
                days_needed = max(long_period * 2, 60)
                price_data = await self.get_stock_data(stock_code, days=days_needed)
                
                if len(price_data) < long_period + 1:
                    continue
                
                # 计算移动平均线
                close_prices = [p['close'] for p in price_data]
                volumes = [p['volume'] for p in price_data]
                
                current_ma_short = self.calculate_ma(close_prices, short_period)
                current_ma_long = self.calculate_ma(close_prices, long_period)
                prev_ma_short = self.calculate_ma(close_prices[1:], short_period)
                prev_ma_long = self.calculate_ma(close_prices[1:], long_period)
                
                if None in [current_ma_short, current_ma_long, prev_ma_short, prev_ma_long]:
                    continue
                
                # 计算平均成交量
                avg_volume = sum(volumes[:10]) / min(10, len(volumes))
                current_volume = volumes[0] if volumes else 0
                
                # 判断交叉信号
                signal = None
                confidence = 0.5
                reason = ""
                
                # 黄金交叉 - 买入信号
                if self.is_golden_cross(current_ma_short, current_ma_long, prev_ma_short, prev_ma_long):
                    signal = 'buy'
                    confidence = 0.7
                    reason = f"短期均线({short_period}日)上穿长期均线({long_period}日)，形成黄金交叉"
                    
                    # 成交量确认
                    if self.is_volume_surge(current_volume, avg_volume, volume_threshold):
                        confidence += 0.2
                        reason += "，伴随放量确认"
                    
                    # 价格位置确认
                    current_price = close_prices[0]
                    if current_price > current_ma_long:
                        confidence += 0.1
                        reason += "，价格位于长期均线之上"
                
                # 死亡交叉 - 卖出信号
                elif self.is_death_cross(current_ma_short, current_ma_long, prev_ma_short, prev_ma_long):
                    signal = 'sell'
                    confidence = 0.7
                    reason = f"短期均线({short_period}日)下穿长期均线({long_period}日)，形成死亡交叉"
                    
                    # 成交量确认
                    if self.is_volume_surge(current_volume, avg_volume, volume_threshold):
                        confidence += 0.2
                        reason += "，伴随放量确认"
                
                # 只返回满足最小置信度的信号
                if signal and confidence >= min_confidence:
                    current_price = close_prices[0]
                    
                    # 计算目标价格和止损价格
                    if signal == 'buy':
                        target_price = current_price * 1.1  # 10%目标收益
                        stop_loss = current_ma_long * 0.95  # 长期均线下方5%止损
                        expected_return = 0.1
                    else:  # sell
                        target_price = current_price * 0.9   # 10%目标下跌
                        stop_loss = current_ma_long * 1.05  # 长期均线上方5%止损
                        expected_return = -0.1
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal=signal,
                        confidence=confidence,
                        reason=reason,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=expected_return,
                        holding_period="1-2周",
                        additional_data={
                            'ma_short': current_ma_short,
                            'ma_long': current_ma_long,
                            'current_price': current_price,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results


class RSIStrategy(BaseStrategy):
    """RSI超买超卖策略
    
    基于RSI指标判断股票的超买超卖状态。
    RSI < 30时买入，RSI > 70时卖出。
    """
    
    def get_description(self) -> str:
        return "基于RSI指标的超买超卖策略，RSI低于30时买入，高于70时卖出"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'rsi_period': {
                'type': int,
                'default': 14,
                'min': 5,
                'max': 30,
                'description': 'RSI计算周期'
            },
            'oversold_threshold': {
                'type': float,
                'default': 30.0,
                'min': 10.0,
                'max': 40.0,
                'description': '超卖阈值'
            },
            'overbought_threshold': {
                'type': float,
                'default': 70.0,
                'min': 60.0,
                'max': 90.0,
                'description': '超买阈值'
            },
            'trend_confirmation': {
                'type': bool,
                'default': True,
                'description': '是否需要趋势确认'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        rsi_period = self.get_parameter('rsi_period', 14)
        oversold_threshold = self.get_parameter('oversold_threshold', 30.0)
        overbought_threshold = self.get_parameter('overbought_threshold', 70.0)
        trend_confirmation = self.get_parameter('trend_confirmation', True)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                days_needed = max(rsi_period * 3, 60)
                price_data = await self.get_stock_data(stock_code, days=days_needed)
                
                if len(price_data) < rsi_period + 10:
                    continue
                
                close_prices = [p['close'] for p in price_data]
                
                # 计算RSI
                current_rsi = self.calculate_rsi(close_prices, rsi_period)
                if current_rsi is None:
                    continue
                
                signal = None
                confidence = 0.5
                reason = ""
                
                # 超卖信号 - 买入
                if current_rsi < oversold_threshold:
                    signal = 'buy'
                    confidence = 0.6 + (oversold_threshold - current_rsi) / oversold_threshold * 0.3
                    reason = f"RSI({current_rsi:.1f})低于超卖线({oversold_threshold})，股票超卖"
                    
                    # 趋势确认
                    if trend_confirmation:
                        ma_20 = self.calculate_ma(close_prices, 20)
                        if ma_20 and close_prices[0] > ma_20:
                            confidence += 0.1
                            reason += "，价格位于20日均线上方"
                
                # 超买信号 - 卖出
                elif current_rsi > overbought_threshold:
                    signal = 'sell'
                    confidence = 0.6 + (current_rsi - overbought_threshold) / (100 - overbought_threshold) * 0.3
                    reason = f"RSI({current_rsi:.1f})高于超买线({overbought_threshold})，股票超买"
                    
                    # 趋势确认
                    if trend_confirmation:
                        ma_20 = self.calculate_ma(close_prices, 20)
                        if ma_20 and close_prices[0] < ma_20:
                            confidence += 0.1
                            reason += "，价格位于20日均线下方"
                
                if signal and confidence >= 0.6:
                    current_price = close_prices[0]
                    
                    # 计算目标价格和止损价格
                    if signal == 'buy':
                        target_price = current_price * 1.08  # 8%目标收益
                        stop_loss = current_price * 0.95    # 5%止损
                        expected_return = 0.08
                    else:  # sell
                        target_price = current_price * 0.92  # 8%目标下跌
                        stop_loss = current_price * 1.05    # 5%止损
                        expected_return = -0.08
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal=signal,
                        confidence=confidence,
                        reason=reason,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=expected_return,
                        holding_period="3-7天",
                        additional_data={
                            'rsi': current_rsi,
                            'current_price': current_price
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略
    
    基于布林带的突破和回归策略。
    价格触及下轨时买入，触及上轨时卖出。
    """
    
    def get_description(self) -> str:
        return "基于布林带的突破策略，价格触及下轨时买入，触及上轨时卖出"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'period': {
                'type': int,
                'default': 20,
                'min': 10,
                'max': 50,
                'description': '布林带周期'
            },
            'std_dev': {
                'type': float,
                'default': 2.0,
                'min': 1.0,
                'max': 3.0,
                'description': '标准差倍数'
            },
            'touch_threshold': {
                'type': float,
                'default': 0.02,
                'min': 0.01,
                'max': 0.05,
                'description': '触及阈值(百分比)'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        period = self.get_parameter('period', 20)
        std_dev = self.get_parameter('std_dev', 2.0)
        touch_threshold = self.get_parameter('touch_threshold', 0.02)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                days_needed = max(period * 2, 60)
                price_data = await self.get_stock_data(stock_code, days=days_needed)
                
                if len(price_data) < period + 5:
                    continue
                
                close_prices = [p['close'] for p in price_data]
                
                # 计算布林带
                bb_data = self.calculate_bollinger_bands(close_prices, period, std_dev)
                if not bb_data:
                    continue
                
                current_price = close_prices[0]
                upper_band = bb_data['upper']
                middle_band = bb_data['middle']
                lower_band = bb_data['lower']
                
                signal = None
                confidence = 0.5
                reason = ""
                
                # 价格接近下轨 - 买入信号
                lower_distance = abs(current_price - lower_band) / lower_band
                if lower_distance <= touch_threshold and current_price <= lower_band * 1.01:
                    signal = 'buy'
                    confidence = 0.7 - lower_distance * 10  # 越接近置信度越高
                    reason = f"价格({current_price:.2f})接近布林带下轨({lower_band:.2f})，超卖反弹机会"
                    
                    # 成交量确认
                    volumes = [p['volume'] for p in price_data]
                    avg_volume = sum(volumes[:10]) / min(10, len(volumes))
                    if volumes[0] > avg_volume * 1.2:
                        confidence += 0.1
                        reason += "，伴随放量"
                
                # 价格接近上轨 - 卖出信号
                upper_distance = abs(current_price - upper_band) / upper_band
                if upper_distance <= touch_threshold and current_price >= upper_band * 0.99:
                    signal = 'sell'
                    confidence = 0.7 - upper_distance * 10  # 越接近置信度越高
                    reason = f"价格({current_price:.2f})接近布林带上轨({upper_band:.2f})，超买回调风险"
                    
                    # 成交量确认
                    volumes = [p['volume'] for p in price_data]
                    avg_volume = sum(volumes[:10]) / min(10, len(volumes))
                    if volumes[0] > avg_volume * 1.2:
                        confidence += 0.1
                        reason += "，伴随放量"
                
                if signal and confidence >= 0.6:
                    # 计算目标价格和止损价格
                    if signal == 'buy':
                        target_price = middle_band  # 目标中轨
                        stop_loss = lower_band * 0.98  # 下轨下方2%止损
                        expected_return = (target_price - current_price) / current_price
                    else:  # sell
                        target_price = middle_band  # 目标中轨
                        stop_loss = upper_band * 1.02  # 上轨上方2%止损
                        expected_return = (target_price - current_price) / current_price
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal=signal,
                        confidence=confidence,
                        reason=reason,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=expected_return,
                        holding_period="1-3天",
                        additional_data={
                            'current_price': current_price,
                            'upper_band': upper_band,
                            'middle_band': middle_band,
                            'lower_band': lower_band,
                            'band_width': (upper_band - lower_band) / middle_band
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results