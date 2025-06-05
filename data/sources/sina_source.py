"""新浪财经数据源

基于新浪财经API的数据源实现，提供实时行情数据。
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import aiohttp
import re
from loguru import logger

from .base import BaseDataSource


class SinaSource(BaseDataSource):
    """新浪财经数据源
    
    主要提供实时行情数据，历史数据支持有限。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://hq.sinajs.cn')
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    def _convert_stock_code(self, code: str) -> str:
        """转换股票代码为新浪格式
        
        Args:
            code: 标准格式代码 (如: 000001.SZ)
            
        Returns:
            新浪格式代码 (如: sz000001)
        """
        if '.' in code:
            symbol, exchange = code.split('.')
            if exchange == 'SZ':
                return f'sz{symbol}'
            elif exchange == 'SH':
                return f'sh{symbol}'
        return code.lower()
    
    def _parse_realtime_data(self, response_text: str, original_codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """解析实时数据响应
        
        Args:
            response_text: 响应文本
            original_codes: 原始股票代码列表
            
        Returns:
            解析后的实时数据
        """
        data = {}
        lines = response_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            if i >= len(original_codes):
                break
                
            original_code = original_codes[i]
            
            # 解析数据行
            match = re.search(r'"([^"]+)"', line)
            if not match:
                continue
                
            fields = match.group(1).split(',')
            if len(fields) < 32:
                continue
            
            try:
                # 解析各字段
                name = fields[0]
                open_price = float(fields[1]) if fields[1] else 0.0
                prev_close = float(fields[2]) if fields[2] else 0.0
                current_price = float(fields[3]) if fields[3] else 0.0
                high = float(fields[4]) if fields[4] else 0.0
                low = float(fields[5]) if fields[5] else 0.0
                
                # 买卖盘
                bid1 = float(fields[6]) if fields[6] else 0.0
                ask1 = float(fields[7]) if fields[7] else 0.0
                
                # 成交量和成交额
                volume = int(fields[8]) if fields[8] else 0
                amount = float(fields[9]) if fields[9] else 0.0
                
                # 计算涨跌
                change = current_price - prev_close if prev_close > 0 else 0.0
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0
                
                # 日期和时间
                trade_date = fields[30] if len(fields) > 30 else ''
                trade_time = fields[31] if len(fields) > 31 else ''
                
                data[original_code] = {
                    'name': name,
                    'current_price': current_price,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'prev_close': prev_close,
                    'change': change,
                    'change_pct': change_pct,
                    'volume': volume,
                    'amount': amount,
                    'bid1': bid1,
                    'ask1': ask1,
                    'trade_date': trade_date,
                    'trade_time': trade_time,
                    'update_time': datetime.now().isoformat()
                }
                
            except (ValueError, IndexError) as e:
                self.logger.warning(f"解析股票 {original_code} 数据失败: {e}")
                continue
        
        return data
    
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表
        
        新浪财经不直接提供股票列表API，返回空列表。
        """
        self.logger.warning("新浪财经不支持获取股票列表")
        return []
    
    async def get_stock_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """获取股票历史数据
        
        新浪财经主要提供实时数据，历史数据支持有限。
        """
        self.logger.warning("新浪财经不支持获取历史数据")
        return []
    
    async def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据"""
        if not self.enabled:
            return {}
        
        if not self._check_rate_limit():
            return {}
        
        if not codes:
            return {}
        
        try:
            session = await self._get_session()
            
            # 转换股票代码
            sina_codes = [self._convert_stock_code(code) for code in codes]
            
            # 构建请求URL
            codes_param = ','.join(sina_codes)
            url = f"{self.base_url}/list={codes_param}"
            
            # 发送请求
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.error(f"请求失败，状态码: {response.status}")
                    return {}
                
                response_text = await response.text(encoding='gbk')
                
                # 解析数据
                data = self._parse_realtime_data(response_text, codes)
                
                self.logger.info(f"获取到 {len(data)} 只股票的实时数据")
                return data
                
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
            return {}
    
    async def get_market_data(
        self,
        index_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """获取市场指数数据"""
        # 新浪财经可以获取指数实时数据
        if not self.enabled:
            return []
        
        try:
            # 转换指数代码
            sina_index_code = self._convert_index_code(index_code)
            if not sina_index_code:
                return []
            
            # 获取实时数据
            realtime_data = await self.get_realtime_data([index_code])
            
            if index_code in realtime_data:
                data = realtime_data[index_code]
                return [{
                    'date': datetime.now().date(),
                    'index_code': index_code,
                    'index_name': data.get('name', ''),
                    'open': data.get('open', 0.0),
                    'high': data.get('high', 0.0),
                    'low': data.get('low', 0.0),
                    'close': data.get('current_price', 0.0),
                    'volume': data.get('volume', 0),
                    'amount': data.get('amount', 0.0),
                    'change_pct': data.get('change_pct', 0.0)
                }]
            
            return []
            
        except Exception as e:
            self.logger.error(f"获取指数数据失败 {index_code}: {e}")
            return []
    
    def _convert_index_code(self, index_code: str) -> Optional[str]:
        """转换指数代码为新浪格式"""
        index_map = {
            '000001.SH': 's_sh000001',
            '399001.SZ': 's_sz399001',
            '399006.SZ': 's_sz399006',
            '000300.SH': 's_sh000300',
            '000905.SH': 's_sh000905',
        }
        return index_map.get(index_code)
    
    async def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票
        
        新浪财经不直接提供搜索API。
        """
        self.logger.warning("新浪财经不支持股票搜索")
        return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.enabled:
            return False
        
        try:
            # 尝试获取上证指数实时数据
            test_data = await self.get_realtime_data(['000001.SH'])
            return len(test_data) > 0
        except Exception as e:
            self.logger.error(f"新浪财经健康检查失败: {e}")
            return False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None