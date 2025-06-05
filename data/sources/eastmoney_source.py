"""东方财富数据源

基于东方财富API的数据源实现，提供股票数据和资金流向数据。
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import aiohttp
import json
from loguru import logger

from .base import BaseDataSource


class EastMoneySource(BaseDataSource):
    """东方财富数据源
    
    提供股票行情、资金流向、板块数据等。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://push2.eastmoney.com')
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://quote.eastmoney.com/'
                }
            )
        return self.session
    
    def _convert_stock_code(self, code: str) -> str:
        """转换股票代码为东方财富格式
        
        Args:
            code: 标准格式代码 (如: 000001.SZ)
            
        Returns:
            东方财富格式代码 (如: 0.000001)
        """
        if '.' in code:
            symbol, exchange = code.split('.')
            if exchange == 'SZ':
                return f'0.{symbol}'
            elif exchange == 'SH':
                return f'1.{symbol}'
        return code
    
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表"""
        if not self.enabled:
            return []
        
        if not self._check_rate_limit():
            return []
        
        try:
            session = await self._get_session()
            
            # 东方财富股票列表API
            url = f"{self.base_url}/api/qt/clist/get"
            params = {
                'pn': 1,
                'pz': 5000,  # 获取5000只股票
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    self.logger.error(f"请求失败，状态码: {response.status}")
                    return []
                
                data = await response.json()
                
                if 'data' not in data or 'diff' not in data['data']:
                    return []
                
                stocks = []
                for item in data['data']['diff']:
                    try:
                        # 解析股票信息
                        code = item.get('f12', '')  # 股票代码
                        name = item.get('f14', '')  # 股票名称
                        
                        # 判断市场
                        market_code = item.get('f13', 0)
                        if market_code == 0:
                            full_code = f"{code}.SZ"
                            market_name = 'SZ'
                        elif market_code == 1:
                            full_code = f"{code}.SH"
                            market_name = 'SH'
                        else:
                            continue
                        
                        stocks.append({
                            'code': full_code,
                            'symbol': code,
                            'name': name,
                            'market': market_name,
                            'industry': '',  # 东方财富此API不提供行业信息
                            'list_date': ''
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"解析股票信息失败: {e}")
                        continue
                
                self.logger.info(f"获取到 {len(stocks)} 只股票")
                return stocks
                
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_stock_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        if not self.enabled:
            return []
        
        if not self._check_rate_limit():
            return []
        
        try:
            session = await self._get_session()
            
            # 转换股票代码
            em_code = self._convert_stock_code(code)
            
            # 构建请求参数
            url = f"{self.base_url}/api/qt/stock/kline/get"
            
            # 周期映射
            period_map = {
                'daily': '101',
                '5min': '5',
                '15min': '15',
                '30min': '30',
                '60min': '60'
            }
            
            klt = period_map.get(period, '101')
            
            params = {
                'secid': em_code,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': klt,
                'fqt': '1',  # 前复权
                'beg': start_date.strftime('%Y%m%d'),
                'end': end_date.strftime('%Y%m%d')
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    self.logger.error(f"请求失败，状态码: {response.status}")
                    return []
                
                data = await response.json()
                
                if 'data' not in data or 'klines' not in data['data']:
                    return []
                
                # 解析K线数据
                stock_data = []
                for kline in data['data']['klines']:
                    try:
                        fields = kline.split(',')
                        if len(fields) < 11:
                            continue
                        
                        # 解析日期
                        if period == 'daily':
                            trade_date = datetime.strptime(fields[0], '%Y-%m-%d').date()
                        else:
                            trade_date = datetime.strptime(fields[0], '%Y-%m-%d %H:%M')
                        
                        stock_data.append({
                            'code': code,
                            'date': trade_date,
                            'open': float(fields[1]),
                            'close': float(fields[2]),
                            'high': float(fields[3]),
                            'low': float(fields[4]),
                            'volume': int(fields[5]),
                            'amount': float(fields[6]),
                            'amplitude': float(fields[7]) if fields[7] else 0.0,
                            'change_pct': float(fields[8]) if fields[8] else 0.0,
                            'change': float(fields[9]) if fields[9] else 0.0,
                            'turnover_rate': float(fields[10]) if fields[10] else 0.0
                        })
                        
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"解析K线数据失败: {e}")
                        continue
                
                self.logger.info(f"获取到股票 {code} {len(stock_data)} 条数据")
                return stock_data
                
        except Exception as e:
            self.logger.error(f"获取股票数据失败 {code}: {e}")
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
            em_codes = [self._convert_stock_code(code) for code in codes]
            
            # 构建请求URL
            url = f"{self.base_url}/api/qt/ulist.np/get"
            params = {
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f62,f128,f136,f115,f152',
                'secids': ','.join(em_codes)
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    self.logger.error(f"请求失败，状态码: {response.status}")
                    return {}
                
                data = await response.json()
                
                if 'data' not in data or 'diff' not in data['data']:
                    return {}
                
                # 解析实时数据
                realtime_data = {}
                for i, item in enumerate(data['data']['diff']):
                    if i >= len(codes):
                        break
                    
                    original_code = codes[i]
                    
                    try:
                        realtime_data[original_code] = {
                            'name': item.get('f14', ''),
                            'current_price': item.get('f2', 0.0),
                            'change': item.get('f4', 0.0),
                            'change_pct': item.get('f3', 0.0),
                            'open': item.get('f17', 0.0),
                            'high': item.get('f15', 0.0),
                            'low': item.get('f16', 0.0),
                            'prev_close': item.get('f18', 0.0),
                            'volume': item.get('f5', 0),
                            'amount': item.get('f6', 0.0),
                            'turnover_rate': item.get('f8', 0.0),
                            'pe_ratio': item.get('f9', 0.0),
                            'pb_ratio': item.get('f23', 0.0),
                            'market_cap': item.get('f20', 0.0),
                            'update_time': datetime.now().isoformat()
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"解析股票 {original_code} 实时数据失败: {e}")
                        continue
                
                self.logger.info(f"获取到 {len(realtime_data)} 只股票的实时数据")
                return realtime_data
                
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
            return {}
    
    async def get_money_flow_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取资金流向数据
        
        Args:
            codes: 股票代码列表
            
        Returns:
            资金流向数据
        """
        if not self.enabled:
            return {}
        
        if not self._check_rate_limit():
            return {}
        
        try:
            session = await self._get_session()
            
            money_flow_data = {}
            
            # 分批获取资金流向数据
            for code in codes:
                try:
                    em_code = self._convert_stock_code(code)
                    
                    url = f"{self.base_url}/api/qt/stock/fflow/get"
                    params = {
                        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                        'invt': 2,
                        'fltt': 2,
                        'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
                        'secid': em_code
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'data' in data and data['data']:
                                flow_data = data['data']
                                money_flow_data[code] = {
                                    'main_net_inflow': flow_data.get('f1', 0.0),  # 主力净流入
                                    'main_net_inflow_rate': flow_data.get('f2', 0.0),  # 主力净流入率
                                    'super_large_net_inflow': flow_data.get('f3', 0.0),  # 超大单净流入
                                    'large_net_inflow': flow_data.get('f5', 0.0),  # 大单净流入
                                    'medium_net_inflow': flow_data.get('f7', 0.0),  # 中单净流入
                                    'small_net_inflow': flow_data.get('f9', 0.0),  # 小单净流入
                                    'update_time': datetime.now().isoformat()
                                }
                    
                    # 避免请求过快
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.logger.warning(f"获取股票 {code} 资金流向失败: {e}")
                    continue
            
            return money_flow_data
            
        except Exception as e:
            self.logger.error(f"获取资金流向数据失败: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.enabled:
            return False
        
        try:
            # 尝试获取少量股票数据
            test_data = await self.get_realtime_data(['000001.SZ'])
            return len(test_data) > 0
        except Exception as e:
            self.logger.error(f"东方财富健康检查失败: {e}")
            return False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None