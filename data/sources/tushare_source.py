"""Tushare数据源

基于Tushare API的数据源实现，提供A股市场数据。
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import pandas as pd
from loguru import logger

try:
    import tushare as ts
except ImportError:
    ts = None
    logger.warning("Tushare未安装，请运行: pip install tushare")

from .base import BaseDataSource


class TushareSource(BaseDataSource):
    """Tushare数据源
    
    提供A股市场的股票数据、指数数据和基本面数据。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = config.get('token')
        self.pro = None
        
        if ts and self.token:
            try:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
                self.logger.info("Tushare API初始化成功")
            except Exception as e:
                self.logger.error(f"Tushare API初始化失败: {e}")
                self.enabled = False
        else:
            self.logger.warning("Tushare token未配置或模块未安装")
            self.enabled = False
    
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表"""
        if not self.enabled or not self.pro:
            return []
        
        if not self._check_rate_limit():
            return []
        
        try:
            # 获取股票基本信息
            if market == 'A':
                # A股市场
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
            else:
                self.logger.warning(f"不支持的市场类型: {market}")
                return []
            
            if df.empty:
                return []
            
            # 转换为标准格式
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row['ts_code'],
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'market': market,
                    'area': row.get('area', ''),
                    'industry': row.get('industry', ''),
                    'list_date': row.get('list_date', '')
                })
            
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
        if not self.enabled or not self.pro:
            return []
        
        if not self._check_rate_limit():
            return []
        
        try:
            # 转换日期格式
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            if period == 'daily':
                # 日线数据
                df = self.pro.daily(
                    ts_code=code,
                    start_date=start_str,
                    end_date=end_str
                )
            elif period in ['5min', '15min', '30min', '60min']:
                # 分钟线数据
                freq_map = {
                    '5min': '5min',
                    '15min': '15min',
                    '30min': '30min',
                    '60min': '60min'
                }
                df = ts.pro_bar(
                    ts_code=code,
                    freq=freq_map[period],
                    start_date=start_str,
                    end_date=end_str
                )
            else:
                self.logger.warning(f"不支持的数据周期: {period}")
                return []
            
            if df.empty:
                return []
            
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 转换为标准格式
            data = []
            for _, row in df.iterrows():
                # 处理日期
                if period == 'daily':
                    trade_date = datetime.strptime(str(row['trade_date']), '%Y%m%d').date()
                else:
                    trade_date = datetime.strptime(str(row['trade_date']), '%Y%m%d %H:%M:%S')
                
                data.append({
                    'code': code,
                    'date': trade_date,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['vol']) if pd.notna(row['vol']) else 0,
                    'amount': float(row['amount']) if pd.notna(row['amount']) else 0.0,
                    'change': float(row.get('change', 0)) if pd.notna(row.get('change')) else 0.0,
                    'pct_chg': float(row.get('pct_chg', 0)) if pd.notna(row.get('pct_chg')) else 0.0
                })
            
            self.logger.info(f"获取到股票 {code} {len(data)} 条数据")
            return data
            
        except Exception as e:
            self.logger.error(f"获取股票数据失败 {code}: {e}")
            return []
    
    async def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据"""
        if not self.enabled or not self.pro:
            return {}
        
        if not self._check_rate_limit():
            return {}
        
        try:
            # Tushare实时数据需要特殊处理
            # 这里使用最新的日线数据作为近似
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            realtime_data = {}
            
            # 分批获取数据（避免单次请求过多）
            batch_size = 50
            for i in range(0, len(codes), batch_size):
                batch_codes = codes[i:i + batch_size]
                
                for code in batch_codes:
                    try:
                        # 获取最新交易日数据
                        df = self.pro.daily(
                            ts_code=code,
                            start_date=yesterday.strftime('%Y%m%d'),
                            end_date=today.strftime('%Y%m%d')
                        )
                        
                        if not df.empty:
                            latest = df.iloc[0]  # 最新数据
                            
                            realtime_data[code] = {
                                'current_price': float(latest['close']),
                                'open': float(latest['open']),
                                'high': float(latest['high']),
                                'low': float(latest['low']),
                                'prev_close': float(latest['pre_close']) if 'pre_close' in latest else float(latest['close']),
                                'volume': int(latest['vol']) if pd.notna(latest['vol']) else 0,
                                'amount': float(latest['amount']) if pd.notna(latest['amount']) else 0.0,
                                'change': float(latest.get('change', 0)) if pd.notna(latest.get('change')) else 0.0,
                                'change_pct': float(latest.get('pct_chg', 0)) if pd.notna(latest.get('pct_chg')) else 0.0,
                                'update_time': datetime.now().isoformat()
                            }
                        
                        # 避免请求过快
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        self.logger.warning(f"获取股票 {code} 实时数据失败: {e}")
                        continue
            
            self.logger.info(f"获取到 {len(realtime_data)} 只股票的实时数据")
            return realtime_data
            
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
        if not self.enabled or not self.pro:
            return []
        
        if not self._check_rate_limit():
            return []
        
        try:
            # 转换日期格式
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            # 获取指数数据
            df = self.pro.index_daily(
                ts_code=index_code,
                start_date=start_str,
                end_date=end_str
            )
            
            if df.empty:
                return []
            
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 转换为标准格式
            data = []
            for _, row in df.iterrows():
                trade_date = datetime.strptime(str(row['trade_date']), '%Y%m%d').date()
                
                data.append({
                    'date': trade_date,
                    'index_code': index_code,
                    'index_name': self._get_index_name(index_code),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['vol']) if pd.notna(row['vol']) else 0,
                    'amount': float(row['amount']) if pd.notna(row['amount']) else 0.0,
                    'change_pct': float(row.get('pct_chg', 0)) if pd.notna(row.get('pct_chg')) else 0.0
                })
            
            self.logger.info(f"获取到指数 {index_code} {len(data)} 条数据")
            return data
            
        except Exception as e:
            self.logger.error(f"获取指数数据失败 {index_code}: {e}")
            return []
    
    async def get_fundamental_data(self, code: str) -> Dict[str, Any]:
        """获取基本面数据"""
        if not self.enabled or not self.pro:
            return {}
        
        if not self._check_rate_limit():
            return {}
        
        try:
            # 获取基本信息
            basic_df = self.pro.stock_basic(
                ts_code=code,
                fields='ts_code,name,industry,market,list_date,delist_date'
            )
            
            # 获取每日基本面指标
            today = datetime.now().date()
            daily_basic_df = self.pro.daily_basic(
                ts_code=code,
                trade_date=today.strftime('%Y%m%d'),
                fields='ts_code,trade_date,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,total_mv,circ_mv'
            )
            
            fundamental_data = {
                'code': code,
                'update_time': datetime.now().isoformat()
            }
            
            # 基本信息
            if not basic_df.empty:
                basic = basic_df.iloc[0]
                fundamental_data.update({
                    'name': basic.get('name', ''),
                    'industry': basic.get('industry', ''),
                    'market': basic.get('market', ''),
                    'list_date': basic.get('list_date', '')
                })
            
            # 财务指标
            if not daily_basic_df.empty:
                daily_basic = daily_basic_df.iloc[0]
                fundamental_data.update({
                    'pe_ratio': float(daily_basic['pe']) if pd.notna(daily_basic['pe']) else None,
                    'pb_ratio': float(daily_basic['pb']) if pd.notna(daily_basic['pb']) else None,
                    'ps_ratio': float(daily_basic['ps']) if pd.notna(daily_basic['ps']) else None,
                    'dividend_yield': float(daily_basic['dv_ratio']) if pd.notna(daily_basic['dv_ratio']) else None,
                    'total_share': float(daily_basic['total_share']) if pd.notna(daily_basic['total_share']) else None,
                    'float_share': float(daily_basic['float_share']) if pd.notna(daily_basic['float_share']) else None,
                    'total_mv': float(daily_basic['total_mv']) if pd.notna(daily_basic['total_mv']) else None,
                    'market_cap': float(daily_basic['circ_mv']) if pd.notna(daily_basic['circ_mv']) else None
                })
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"获取基本面数据失败 {code}: {e}")
            return {}
    
    def _get_index_name(self, index_code: str) -> str:
        """获取指数名称"""
        index_names = {
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指',
            '000300.SH': '沪深300',
            '000905.SH': '中证500',
            '399905.SZ': '中证500',
        }
        return index_names.get(index_code, index_code)
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.enabled or not self.pro:
            return False
        
        try:
            # 尝试获取少量数据
            df = self.pro.stock_basic(list_status='L', fields='ts_code')
            return not df.empty
        except Exception as e:
            self.logger.error(f"Tushare健康检查失败: {e}")
            return False