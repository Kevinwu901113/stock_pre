from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from loguru import logger


class BaseStrategy(ABC):
    """策略基类
    
    所有策略都应该继承这个基类并实现必要的方法。
    """
    
    def __init__(self, db: Session, parameters: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            db: 数据库会话
            parameters: 策略参数
        """
        self.db = db
        self.parameters = parameters
        self.name = self.__class__.__name__
        self.logger = logger.bind(strategy=self.name)
    
    @abstractmethod
    async def execute(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        执行策略
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            策略执行结果列表，每个结果包含：
            - stock_code: 股票代码
            - signal: 信号类型 ('buy', 'sell', 'hold')
            - confidence: 置信度 (0-1)
            - reason: 推荐理由
            - target_price: 目标价格(可选)
            - stop_loss: 止损价格(可选)
            - expected_return: 预期收益率(可选)
            - holding_period: 建议持有期(可选)
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            策略描述文本
        """
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数模式
        
        Returns:
            参数模式定义，包含参数名称、类型、默认值、范围等
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        验证参数有效性
        
        Returns:
            参数是否有效
        """
        schema = self.get_parameters_schema()
        
        for param_name, param_config in schema.items():
            if param_config.get('required', False) and param_name not in self.parameters:
                self.logger.error(f"缺少必要参数: {param_name}")
                return False
            
            if param_name in self.parameters:
                value = self.parameters[param_name]
                param_type = param_config.get('type')
                
                # 类型检查
                if param_type and not isinstance(value, param_type):
                    self.logger.error(f"参数{param_name}类型错误，期望{param_type}，实际{type(value)}")
                    return False
                
                # 范围检查
                if 'min' in param_config and value < param_config['min']:
                    self.logger.error(f"参数{param_name}小于最小值{param_config['min']}")
                    return False
                
                if 'max' in param_config and value > param_config['max']:
                    self.logger.error(f"参数{param_name}大于最大值{param_config['max']}")
                    return False
        
        return True
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        获取参数值
        
        Args:
            name: 参数名称
            default: 默认值
            
        Returns:
            参数值
        """
        return self.parameters.get(name, default)
    
    def log_execution_start(self, stock_count: int):
        """
        记录策略执行开始
        
        Args:
            stock_count: 股票数量
        """
        self.logger.info(f"策略执行开始，股票数量: {stock_count}，参数: {self.parameters}")
    
    def log_execution_end(self, results_count: int, execution_time: float):
        """
        记录策略执行结束
        
        Args:
            results_count: 结果数量
            execution_time: 执行时间(秒)
        """
        self.logger.info(f"策略执行完成，信号数量: {results_count}，执行时间: {execution_time:.2f}秒")
    
    def create_signal(
        self,
        stock_code: str,
        signal: str,
        confidence: float,
        reason: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        expected_return: Optional[float] = None,
        holding_period: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建策略信号
        
        Args:
            stock_code: 股票代码
            signal: 信号类型
            confidence: 置信度
            reason: 推荐理由
            target_price: 目标价格
            stop_loss: 止损价格
            expected_return: 预期收益率
            holding_period: 建议持有期
            additional_data: 额外数据
            
        Returns:
            策略信号字典
        """
        signal_data = {
            'stock_code': stock_code,
            'signal': signal,
            'confidence': max(0, min(1, confidence)),  # 确保在0-1范围内
            'reason': reason,
            'strategy_name': self.name,
            'generated_at': datetime.now().isoformat()
        }
        
        if target_price is not None:
            signal_data['target_price'] = target_price
        
        if stop_loss is not None:
            signal_data['stop_loss'] = stop_loss
        
        if expected_return is not None:
            signal_data['expected_return'] = expected_return
        
        if holding_period is not None:
            signal_data['holding_period'] = holding_period
        
        if additional_data:
            signal_data.update(additional_data)
        
        return signal_data
    
    async def get_stock_data(
        self,
        stock_code: str,
        days: int = 30,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            days: 天数
            end_date: 结束日期
            
        Returns:
            股票价格数据列表
        """
        from app.models.stock import StockPrice
        from sqlalchemy import and_, desc
        
        if not end_date:
            end_date = date.today()
        
        start_date = end_date - datetime.timedelta(days=days)
        
        prices = self.db.query(StockPrice).filter(
            and_(
                StockPrice.stock_code == stock_code,
                StockPrice.trade_date >= start_date,
                StockPrice.trade_date <= end_date
            )
        ).order_by(desc(StockPrice.trade_date)).all()
        
        return [
            {
                'date': price.trade_date,
                'open': price.open_price,
                'high': price.high_price,
                'low': price.low_price,
                'close': price.close_price,
                'volume': price.volume,
                'amount': price.amount,
                'turnover_rate': price.turnover_rate
            }
            for price in prices
        ]
    
    async def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票基本信息
        """
        from app.models.stock import Stock
        
        stock = self.db.query(Stock).filter(Stock.code == stock_code).first()
        
        if not stock:
            return None
        
        return {
            'code': stock.code,
            'name': stock.name,
            'industry': stock.industry,
            'market': stock.market,
            'list_date': stock.list_date,
            'market_cap': stock.market_cap,
            'pe_ratio': stock.pe_ratio,
            'pb_ratio': stock.pb_ratio
        }
    
    def calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            移动平均值
        """
        if len(prices) < period:
            return None
        
        return sum(prices[:period]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        计算RSI指标
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            RSI值
        """
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
    
    def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2
    ) -> Optional[Dict[str, float]]:
        """
        计算布林带
        
        Args:
            prices: 价格列表
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            布林带数据 {upper, middle, lower}
        """
        if len(prices) < period:
            return None
        
        # 计算中轨(移动平均)
        middle = sum(prices[:period]) / period
        
        # 计算标准差
        variance = sum((p - middle) ** 2 for p in prices[:period]) / period
        std = variance ** 0.5
        
        # 计算上下轨
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, float]]:
        """
        计算MACD指标
        
        Args:
            prices: 价格列表
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            MACD数据 {macd, signal, histogram}
        """
        if len(prices) < slow_period:
            return None
        
        # 计算EMA
        def calculate_ema(data: List[float], period: int) -> float:
            multiplier = 2 / (period + 1)
            ema = data[0]
            for price in data[1:period]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            return ema
        
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        
        # 简化实现，实际需要计算信号线
        return {
            'macd': macd_line,
            'signal': 0,  # 需要更复杂的计算
            'histogram': macd_line
        }
    
    def is_golden_cross(self, ma_short: float, ma_long: float, prev_ma_short: float, prev_ma_long: float) -> bool:
        """
        判断是否为黄金交叉
        
        Args:
            ma_short: 短期均线当前值
            ma_long: 长期均线当前值
            prev_ma_short: 短期均线前一值
            prev_ma_long: 长期均线前一值
            
        Returns:
            是否为黄金交叉
        """
        return (prev_ma_short <= prev_ma_long) and (ma_short > ma_long)
    
    def is_death_cross(self, ma_short: float, ma_long: float, prev_ma_short: float, prev_ma_long: float) -> bool:
        """
        判断是否为死亡交叉
        
        Args:
            ma_short: 短期均线当前值
            ma_long: 长期均线当前值
            prev_ma_short: 短期均线前一值
            prev_ma_long: 长期均线前一值
            
        Returns:
            是否为死亡交叉
        """
        return (prev_ma_short >= prev_ma_long) and (ma_short < ma_long)
    
    def calculate_price_change_rate(self, current_price: float, previous_price: float) -> float:
        """
        计算价格变化率
        
        Args:
            current_price: 当前价格
            previous_price: 前一价格
            
        Returns:
            价格变化率(百分比)
        """
        if previous_price == 0:
            return 0
        
        return ((current_price - previous_price) / previous_price) * 100
    
    def is_volume_surge(self, current_volume: int, avg_volume: float, threshold: float = 2.0) -> bool:
        """
        判断是否为放量
        
        Args:
            current_volume: 当前成交量
            avg_volume: 平均成交量
            threshold: 放量阈值倍数
            
        Returns:
            是否为放量
        """
        return current_volume > (avg_volume * threshold)
    
    def calculate_support_resistance(
        self,
        prices: List[Dict[str, Any]],
        window: int = 5
    ) -> Dict[str, List[float]]:
        """
        计算支撑位和阻力位
        
        Args:
            prices: 价格数据列表
            window: 窗口大小
            
        Returns:
            支撑位和阻力位列表
        """
        if len(prices) < window * 2 + 1:
            return {'support': [], 'resistance': []}
        
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(prices) - window):
            # 检查是否为局部最低点(支撑位)
            is_local_min = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j]['low'] < prices[i]['low']:
                    is_local_min = False
                    break
            
            if is_local_min:
                support_levels.append(prices[i]['low'])
            
            # 检查是否为局部最高点(阻力位)
            is_local_max = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j]['high'] > prices[i]['high']:
                    is_local_max = False
                    break
            
            if is_local_max:
                resistance_levels.append(prices[i]['high'])
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }