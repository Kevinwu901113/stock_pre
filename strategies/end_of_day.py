from typing import List, Dict, Any
from datetime import datetime, time, timedelta
from .base import BaseStrategy
from loguru import logger
import pandas as pd


class EndOfDayStrategy(BaseStrategy):
    """尾盘买入策略
    
    在收盘前30分钟（14:30-15:00）分析股票，寻找符合条件的买入机会：
    1. 连续上涨趋势
    2. 成交量放大
    3. 技术指标突破
    4. 尾盘拉升
    """
    
    def get_description(self) -> str:
        return "尾盘买入策略：在收盘前30分钟寻找连续上涨、成交量放大、技术指标突破的股票进行买入推荐"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'consecutive_days': {
                'type': int,
                'default': 2,
                'min': 1,
                'max': 5,
                'description': '连续上涨天数要求'
            },
            'volume_ratio': {
                'type': float,
                'default': 1.5,
                'min': 1.0,
                'max': 3.0,
                'description': '成交量放大倍数'
            },
            'price_increase_threshold': {
                'type': float,
                'default': 0.02,
                'min': 0.01,
                'max': 0.1,
                'description': '单日涨幅阈值'
            },
            'rsi_threshold': {
                'type': float,
                'default': 70,
                'min': 50,
                'max': 80,
                'description': 'RSI突破阈值'
            },
            'ma_period': {
                'type': int,
                'default': 20,
                'min': 5,
                'max': 60,
                'description': '移动平均线周期'
            },
            'min_confidence': {
                'type': float,
                'default': 0.7,
                'min': 0.5,
                'max': 1.0,
                'description': '最小置信度'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """执行尾盘买入策略"""
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        # 获取参数
        consecutive_days = self.get_parameter('consecutive_days', 2)
        volume_ratio = self.get_parameter('volume_ratio', 1.5)
        price_increase_threshold = self.get_parameter('price_increase_threshold', 0.02)
        rsi_threshold = self.get_parameter('rsi_threshold', 70)
        ma_period = self.get_parameter('ma_period', 20)
        min_confidence = self.get_parameter('min_confidence', 0.7)
        
        results = []
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                days_needed = max(ma_period * 2, 60)
                price_data = await self.get_stock_data(stock_code, days=days_needed)
                
                if len(price_data) < ma_period + consecutive_days:
                    continue
                
                # 分析股票
                analysis_result = await self._analyze_stock(stock_code, price_data, {
                    'consecutive_days': consecutive_days,
                    'volume_ratio': volume_ratio,
                    'price_increase_threshold': price_increase_threshold,
                    'rsi_threshold': rsi_threshold,
                    'ma_period': ma_period,
                    'min_confidence': min_confidence
                })
                
                if analysis_result and analysis_result['confidence'] >= min_confidence:
                    results.append(analysis_result)
                    
            except Exception as e:
                self.logger.error(f"分析股票 {stock_code} 失败: {str(e)}")
                continue
        
        self.log_execution_end(start_time, len(results))
        return results
    
    async def _analyze_stock(self, stock_code: str, price_data: List[Dict], params: Dict) -> Optional[Dict[str, Any]]:
        """分析单只股票"""
        try:
            # 转换为DataFrame便于计算
            df = pd.DataFrame(price_data)
            df = df.sort_values('trade_date')
            
            # 计算技术指标
            df['price_change'] = df['close'].pct_change()
            df['ma'] = df['close'].rolling(window=params['ma_period']).mean()
            df['rsi'] = self._calculate_rsi(df['close'], 14)
            df['volume_ma'] = df['volume'].rolling(window=10).mean()
            
            # 获取最新数据
            latest = df.iloc[-1]
            recent_data = df.tail(params['consecutive_days'] + 1)
            
            # 检查条件
            signals = []
            confidence_factors = []
            
            # 1. 连续上涨检查
            consecutive_up = self._check_consecutive_increase(
                recent_data, params['consecutive_days'], params['price_increase_threshold']
            )
            if consecutive_up['is_consecutive']:
                signals.append(f"连续{consecutive_up['days']}天上涨")
                confidence_factors.append(0.3)
            
            # 2. 成交量放大检查
            volume_surge = self._check_volume_surge(latest, params['volume_ratio'])
            if volume_surge['is_surge']:
                signals.append(f"成交量放大{volume_surge['ratio']:.1f}倍")
                confidence_factors.append(0.25)
            
            # 3. 技术指标突破
            technical_signals = self._check_technical_breakthrough(df, params)
            signals.extend(technical_signals['signals'])
            confidence_factors.extend(technical_signals['confidence_factors'])
            
            # 4. 尾盘拉升检查（如果有分时数据）
            end_of_day_surge = await self._check_end_of_day_surge(stock_code)
            if end_of_day_surge['is_surge']:
                signals.append("尾盘拉升")
                confidence_factors.append(0.2)
            
            # 计算总置信度
            total_confidence = min(sum(confidence_factors), 1.0) if confidence_factors else 0.0
            
            if total_confidence >= params['min_confidence'] and len(signals) >= 2:
                # 计算目标价和止损价
                current_price = latest['close']
                target_price = current_price * 1.08  # 8%目标收益
                stop_loss_price = current_price * 0.95  # 5%止损
                
                return {
                    'stock_code': stock_code,
                    'signal': 'buy',
                    'confidence': total_confidence,
                    'reason': f"尾盘买入信号：{'; '.join(signals)}",
                    'target_price': target_price,
                    'stop_loss': stop_loss_price,
                    'expected_return': 0.08,
                    'holding_period': '1-3天',
                    'signal_type': 'end_of_day_buy',
                    'strategy_name': 'end_of_day',
                    'created_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(hours=18)  # 次日收盘前过期
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 失败: {str(e)}")
            return None
    
    def _check_consecutive_increase(self, data: pd.DataFrame, days: int, threshold: float) -> Dict:
        """检查连续上涨"""
        try:
            price_changes = data['price_change'].dropna()
            consecutive_count = 0
            
            for change in price_changes.tail(days):
                if change >= threshold:
                    consecutive_count += 1
                else:
                    break
            
            return {
                'is_consecutive': consecutive_count >= days,
                'days': consecutive_count
            }
        except:
            return {'is_consecutive': False, 'days': 0}
    
    def _check_volume_surge(self, latest_data: pd.Series, ratio_threshold: float) -> Dict:
        """检查成交量放大"""
        try:
            current_volume = latest_data['volume']
            avg_volume = latest_data['volume_ma']
            
            if pd.isna(avg_volume) or avg_volume == 0:
                return {'is_surge': False, 'ratio': 0}
            
            volume_ratio = current_volume / avg_volume
            
            return {
                'is_surge': volume_ratio >= ratio_threshold,
                'ratio': volume_ratio
            }
        except:
            return {'is_surge': False, 'ratio': 0}
    
    def _check_technical_breakthrough(self, df: pd.DataFrame, params: Dict) -> Dict:
        """检查技术指标突破"""
        signals = []
        confidence_factors = []
        
        try:
            latest = df.iloc[-1]
            
            # RSI突破
            if not pd.isna(latest['rsi']) and latest['rsi'] > params['rsi_threshold']:
                signals.append(f"RSI突破{params['rsi_threshold']}")
                confidence_factors.append(0.15)
            
            # 价格突破均线
            if not pd.isna(latest['ma']) and latest['close'] > latest['ma']:
                breakthrough_ratio = (latest['close'] - latest['ma']) / latest['ma']
                if breakthrough_ratio > 0.02:  # 突破2%以上
                    signals.append(f"突破{params['ma_period']}日均线")
                    confidence_factors.append(0.2)
            
            return {
                'signals': signals,
                'confidence_factors': confidence_factors
            }
        except:
            return {'signals': [], 'confidence_factors': []}
    
    async def _check_end_of_day_surge(self, stock_code: str) -> Dict:
        """检查尾盘拉升（简化版本）"""
        # 这里可以接入实时数据API检查尾盘表现
        # 暂时返回默认值
        return {'is_surge': False}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)


class MorningExitStrategy(BaseStrategy):
    """早盘卖出策略
    
    在开盘后30分钟（9:30-10:00）分析持有股票，决定是否卖出：
    1. 达到目标收益
    2. 触发止损
    3. 技术指标转弱
    4. 开盘跳空
    """
    
    def get_description(self) -> str:
        return "早盘卖出策略：在开盘后30分钟分析持有股票，根据收益情况和技术指标决定是否卖出"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            'profit_target': {
                'type': float,
                'default': 0.05,
                'min': 0.02,
                'max': 0.15,
                'description': '目标收益率'
            },
            'stop_loss': {
                'type': float,
                'default': 0.03,
                'min': 0.01,
                'max': 0.1,
                'description': '止损比例'
            },
            'gap_threshold': {
                'type': float,
                'default': 0.03,
                'min': 0.01,
                'max': 0.1,
                'description': '跳空阈值'
            },
            'rsi_exit_threshold': {
                'type': float,
                'default': 80,
                'min': 70,
                'max': 90,
                'description': 'RSI卖出阈值'
            },
            'min_confidence': {
                'type': float,
                'default': 0.6,
                'min': 0.5,
                'max': 1.0,
                'description': '最小置信度'
            }
        }
    
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """执行早盘卖出策略"""
        start_time = datetime.now()
        self.log_execution_start(len(stock_codes))
        
        if not self.validate_parameters():
            return []
        
        # 获取参数
        profit_target = self.get_parameter('profit_target', 0.05)
        stop_loss = self.get_parameter('stop_loss', 0.03)
        gap_threshold = self.get_parameter('gap_threshold', 0.03)
        rsi_exit_threshold = self.get_parameter('rsi_exit_threshold', 80)
        min_confidence = self.get_parameter('min_confidence', 0.6)
        
        results = []
        
        # 获取持有的股票（从推荐记录中获取）
        held_stocks = await self._get_held_stocks(stock_codes)
        
        for stock_info in held_stocks:
            try:
                stock_code = stock_info['stock_code']
                buy_price = stock_info['buy_price']
                
                # 获取当前价格数据
                price_data = await self.get_stock_data(stock_code, days=30)
                
                if not price_data:
                    continue
                
                # 分析是否应该卖出
                analysis_result = await self._analyze_exit_signal(
                    stock_code, price_data, buy_price, {
                        'profit_target': profit_target,
                        'stop_loss': stop_loss,
                        'gap_threshold': gap_threshold,
                        'rsi_exit_threshold': rsi_exit_threshold,
                        'min_confidence': min_confidence
                    }
                )
                
                if analysis_result and analysis_result['confidence'] >= min_confidence:
                    results.append(analysis_result)
                    
            except Exception as e:
                self.logger.error(f"分析股票 {stock_info.get('stock_code', 'unknown')} 卖出信号失败: {str(e)}")
                continue
        
        self.log_execution_end(start_time, len(results))
        return results
    
    async def _get_held_stocks(self, stock_codes: List[str]) -> List[Dict]:
        """获取持有的股票信息"""
        try:
            # 从数据库查询昨日买入的推荐
            from app.models.stock import Recommendation
            
            yesterday = datetime.now().date() - timedelta(days=1)
            
            held_stocks = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.recommendation_type == 'buy',
                    Recommendation.created_at >= yesterday,
                    Recommendation.is_active == True,
                    Recommendation.stock_code.in_(stock_codes)
                )
            ).all()
            
            result = []
            for rec in held_stocks:
                # 获取买入价格（可以从推荐的目标价格或当时的收盘价获取）
                price_data = await self.get_stock_data(rec.stock_code, days=1)
                buy_price = price_data[0]['close'] if price_data else None
                
                if buy_price:
                    result.append({
                        'stock_code': rec.stock_code,
                        'buy_price': buy_price,
                        'recommendation_id': rec.id,
                        'buy_date': rec.created_at.date()
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取持有股票失败: {str(e)}")
            return []
    
    async def _analyze_exit_signal(self, stock_code: str, price_data: List[Dict], 
                                 buy_price: float, params: Dict) -> Optional[Dict[str, Any]]:
        """分析卖出信号"""
        try:
            if not price_data:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(price_data)
            df = df.sort_values('trade_date')
            
            # 计算技术指标
            df['rsi'] = self._calculate_rsi(df['close'], 14)
            
            # 获取最新数据
            latest = df.iloc[-1]
            current_price = latest['close']
            
            # 计算收益率
            return_rate = (current_price - buy_price) / buy_price
            
            signals = []
            confidence_factors = []
            
            # 1. 达到目标收益
            if return_rate >= params['profit_target']:
                signals.append(f"达到目标收益{return_rate:.2%}")
                confidence_factors.append(0.4)
            
            # 2. 触发止损
            elif return_rate <= -params['stop_loss']:
                signals.append(f"触发止损{return_rate:.2%}")
                confidence_factors.append(0.5)
            
            # 3. 检查跳空
            if len(df) >= 2:
                prev_close = df.iloc[-2]['close']
                gap_ratio = (latest['open'] - prev_close) / prev_close
                
                if abs(gap_ratio) >= params['gap_threshold']:
                    if gap_ratio > 0:
                        signals.append(f"高开{gap_ratio:.2%}，获利了结")
                        confidence_factors.append(0.3)
                    else:
                        signals.append(f"低开{gap_ratio:.2%}，止损离场")
                        confidence_factors.append(0.4)
            
            # 4. RSI过热
            if not pd.isna(latest['rsi']) and latest['rsi'] >= params['rsi_exit_threshold']:
                signals.append(f"RSI过热({latest['rsi']:.1f})")
                confidence_factors.append(0.2)
            
            # 计算总置信度
            total_confidence = min(sum(confidence_factors), 1.0) if confidence_factors else 0.0
            
            if total_confidence >= params['min_confidence'] and signals:
                return {
                    'stock_code': stock_code,
                    'signal': 'sell',
                    'confidence': total_confidence,
                    'reason': f"早盘卖出信号：{'; '.join(signals)}",
                    'current_price': current_price,
                    'buy_price': buy_price,
                    'return_rate': return_rate,
                    'signal_type': 'morning_exit',
                    'strategy_name': 'morning_exit',
                    'created_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(hours=6)  # 当日收盘前过期
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 卖出信号失败: {str(e)}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)