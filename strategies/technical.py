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


class ComprehensiveTechnicalStrategy(BaseStrategy):
    """综合技术策略
    
    结合多个技术指标进行综合分析：
    1. 收盘价突破五日均线
    2. MACD金叉信号
    3. 换手率高于设定阈值
    4. 成交量放大确认
    """
    
    def get_description(self) -> str:
        return "综合技术策略：收盘价突破五日均线+MACD金叉+换手率确认的多重信号策略"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'ma_period': {
                'type': int,
                'default': 5,
                'min': 3,
                'max': 10,
                'description': '移动平均线周期'
            },
            'turnover_threshold': {
                'type': float,
                'default': 5.0,
                'min': 2.0,
                'max': 15.0,
                'description': '换手率阈值(%)'
            },
            'volume_threshold': {
                'type': float,
                'default': 1.5,
                'min': 1.0,
                'max': 3.0,
                'description': '成交量放大倍数'
            },
            'macd_fast': {
                'type': int,
                'default': 12,
                'min': 8,
                'max': 16,
                'description': 'MACD快线周期'
            },
            'macd_slow': {
                'type': int,
                'default': 26,
                'min': 20,
                'max': 35,
                'description': 'MACD慢线周期'
            },
            'macd_signal': {
                'type': int,
                'default': 9,
                'min': 6,
                'max': 12,
                'description': 'MACD信号线周期'
            },
            'min_confidence': {
                'type': float,
                'default': 0.7,
                'min': 0.5,
                'max': 1.0,
                'description': '最小置信度阈值'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        ma_period = self.get_parameter('ma_period', 5)
        turnover_threshold = self.get_parameter('turnover_threshold', 5.0)
        volume_threshold = self.get_parameter('volume_threshold', 1.5)
        macd_fast = self.get_parameter('macd_fast', 12)
        macd_slow = self.get_parameter('macd_slow', 26)
        macd_signal = self.get_parameter('macd_signal', 9)
        min_confidence = self.get_parameter('min_confidence', 0.7)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取足够的历史数据
                days_needed = max(macd_slow * 2, 60)
                price_data = await self.get_stock_data(stock_code, days=days_needed)
                
                if len(price_data) < macd_slow + 10:
                    continue
                
                close_prices = [p['close'] for p in price_data]
                volumes = [p['volume'] for p in price_data]
                turnover_rates = [p.get('turnover_rate', 0) for p in price_data]
                
                # 1. 检查收盘价突破五日均线
                current_price = close_prices[0]
                ma_5 = self.calculate_ma(close_prices, ma_period)
                prev_ma_5 = self.calculate_ma(close_prices[1:], ma_period)
                
                if not ma_5 or not prev_ma_5:
                    continue
                
                # 突破条件：当前价格高于均线，且前一日价格低于均线
                price_breakthrough = (current_price > ma_5 and 
                                    close_prices[1] <= prev_ma_5)
                
                if not price_breakthrough:
                    continue
                
                # 2. 检查MACD金叉
                macd_data = self.calculate_enhanced_macd(close_prices, macd_fast, macd_slow, macd_signal)
                if not macd_data:
                    continue
                
                macd_golden_cross = self.check_macd_golden_cross(close_prices, macd_fast, macd_slow, macd_signal)
                
                # 3. 检查换手率
                current_turnover = turnover_rates[0] if turnover_rates[0] else 0
                turnover_condition = current_turnover >= turnover_threshold
                
                # 4. 检查成交量放大
                avg_volume = sum(volumes[1:11]) / min(10, len(volumes[1:]))
                current_volume = volumes[0] if volumes else 0
                volume_surge = current_volume >= avg_volume * volume_threshold
                
                # 计算综合信号强度
                signal_strength = 0
                reasons = []
                
                # 价格突破权重：30%
                if price_breakthrough:
                    signal_strength += 0.3
                    breakthrough_pct = ((current_price - ma_5) / ma_5) * 100
                    reasons.append(f"收盘价({current_price:.2f})突破{ma_period}日均线({ma_5:.2f})，涨幅{breakthrough_pct:.1f}%")
                
                # MACD金叉权重：25%
                if macd_golden_cross:
                    signal_strength += 0.25
                    reasons.append(f"MACD形成金叉信号，MACD值{macd_data['macd']:.4f}")
                
                # 换手率权重：25%
                if turnover_condition:
                    signal_strength += 0.25
                    reasons.append(f"换手率{current_turnover:.1f}%高于阈值{turnover_threshold}%")
                
                # 成交量权重：20%
                if volume_surge:
                    signal_strength += 0.2
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                    reasons.append(f"成交量放大{volume_ratio:.1f}倍")
                
                # 只有满足最小条件数量和置信度的才推荐
                conditions_met = sum([price_breakthrough, macd_golden_cross, turnover_condition, volume_surge])
                
                if conditions_met >= 3 and signal_strength >= min_confidence:
                    # 计算目标价格和止损价格
                    target_price = current_price * 1.12  # 12%目标收益
                    stop_loss = ma_5 * 0.97  # 均线下方3%止损
                    expected_return = 0.12
                    
                    # 根据信号强度调整置信度
                    confidence = min(0.95, signal_strength + 0.1)
                    
                    reason = "； ".join(reasons)
                    
                    signal_data = self.create_signal(
                        stock_code=stock_code,
                        signal='buy',
                        confidence=confidence,
                        reason=f"综合技术信号：{reason}",
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=expected_return,
                        holding_period="1-3天",
                        additional_data={
                            'signal_strength': signal_strength,
                            'conditions_met': conditions_met,
                            'current_price': current_price,
                            'ma_5': ma_5,
                            'turnover_rate': current_turnover,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                            'macd_data': macd_data,
                            'signal_type': 'end_of_day_buy'
                        }
                    )
                    
                    results.append(signal_data)
                    
            except Exception as e:
                self.logger.error(f"处理股票{stock_code}时出错: {str(e)}")
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.log_execution_end(len(results), execution_time)
        
        return results
    
    def calculate_enhanced_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, float]]:
        """增强版MACD计算"""
        if len(prices) < slow_period + signal_period:
            return None
        
        # 计算EMA
        def calculate_ema_series(data: List[float], period: int) -> List[float]:
            multiplier = 2 / (period + 1)
            ema_values = [data[0]]
            
            for i in range(1, len(data)):
                ema = (data[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                ema_values.append(ema)
            
            return ema_values
        
        # 计算快慢EMA
        ema_fast_series = calculate_ema_series(prices, fast_period)
        ema_slow_series = calculate_ema_series(prices, slow_period)
        
        # 计算MACD线
        macd_line = ema_fast_series[0] - ema_slow_series[0]
        
        # 计算信号线（MACD的EMA）
        if len(prices) >= slow_period + signal_period:
            macd_series = [ema_fast_series[i] - ema_slow_series[i] for i in range(len(ema_fast_series))]
            signal_line_series = calculate_ema_series(macd_series, signal_period)
            signal_line = signal_line_series[0]
        else:
            signal_line = 0
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def check_macd_golden_cross(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> bool:
        """检查MACD金叉"""
        if len(prices) < slow_period + signal_period + 1:
            return False
        
        # 当前MACD
        current_macd = self.calculate_enhanced_macd(prices, fast_period, slow_period, signal_period)
        # 前一日MACD
        prev_macd = self.calculate_enhanced_macd(prices[1:], fast_period, slow_period, signal_period)
        
        if not current_macd or not prev_macd:
            return False
        
        # 金叉条件：MACD线从下方穿越信号线
        golden_cross = (current_macd['macd'] > current_macd['signal'] and 
                       prev_macd['macd'] <= prev_macd['signal'])
        
        # 额外条件：MACD柱状图为正且增长
        histogram_positive = current_macd['histogram'] > 0
        histogram_growing = current_macd['histogram'] > prev_macd['histogram']
        
        return golden_cross and histogram_positive and histogram_growing