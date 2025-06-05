"""CSV数据源

基于本地CSV文件的数据源实现，作为备用数据方案。
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import os
import pandas as pd
from pathlib import Path
from loguru import logger

from .base import BaseDataSource
from config.settings import settings


class CSVSource(BaseDataSource):
    """CSV数据源
    
    从本地CSV文件读取股票数据，支持多种文件格式。
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.data_dir = Path(config.get('data_dir', settings.CSV_DATA_DIR))
        self.stock_list_file = self.data_dir / 'stock_list.csv'
        self.daily_data_dir = self.data_dir / 'daily'
        self.realtime_data_file = self.data_dir / 'realtime.csv'
        self.fundamental_data_dir = self.data_dir / 'fundamental'
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.daily_data_dir.mkdir(parents=True, exist_ok=True)
            self.fundamental_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建示例文件
            self._create_sample_files()
            
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            self.enabled = False
    
    def _create_sample_files(self):
        """创建示例文件"""
        try:
            # 创建股票列表示例文件
            if not self.stock_list_file.exists():
                sample_stocks = pd.DataFrame({
                    'code': ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH'],
                    'symbol': ['000001', '000002', '600000', '600036'],
                    'name': ['平安银行', '万科A', '浦发银行', '招商银行'],
                    'market': ['SZ', 'SZ', 'SH', 'SH'],
                    'industry': ['银行', '房地产', '银行', '银行'],
                    'list_date': ['19910403', '19910129', '19990910', '20020408']
                })
                sample_stocks.to_csv(self.stock_list_file, index=False, encoding='utf-8')
                self.logger.info(f"创建示例股票列表文件: {self.stock_list_file}")
            
            # 创建实时数据示例文件
            if not self.realtime_data_file.exists():
                sample_realtime = pd.DataFrame({
                    'code': ['000001.SZ', '000002.SZ'],
                    'name': ['平安银行', '万科A'],
                    'current_price': [10.50, 18.20],
                    'change': [0.15, -0.30],
                    'change_pct': [1.45, -1.62],
                    'open': [10.40, 18.50],
                    'high': [10.60, 18.60],
                    'low': [10.30, 18.10],
                    'prev_close': [10.35, 18.50],
                    'volume': [1000000, 800000],
                    'amount': [10500000.0, 14560000.0],
                    'update_time': [datetime.now().isoformat(), datetime.now().isoformat()]
                })
                sample_realtime.to_csv(self.realtime_data_file, index=False, encoding='utf-8')
                self.logger.info(f"创建示例实时数据文件: {self.realtime_data_file}")
                
        except Exception as e:
            self.logger.warning(f"创建示例文件失败: {e}")
    
    def _get_stock_csv_file(self, code: str) -> Path:
        """获取股票CSV文件路径
        
        Args:
            code: 股票代码
            
        Returns:
            CSV文件路径
        """
        return self.daily_data_dir / f"{code}.csv"
    
    def _get_fundamental_csv_file(self, code: str) -> Path:
        """获取基本面数据CSV文件路径
        
        Args:
            code: 股票代码
            
        Returns:
            CSV文件路径
        """
        return self.fundamental_data_dir / f"{code}_fundamental.csv"
    
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表"""
        if not self.enabled:
            return []
        
        try:
            if not self.stock_list_file.exists():
                self.logger.warning(f"股票列表文件不存在: {self.stock_list_file}")
                return []
            
            df = pd.read_csv(self.stock_list_file, encoding='utf-8')
            
            # 筛选市场
            if market == 'A':
                df = df[df['market'].isin(['SH', 'SZ'])]
            elif market in ['SH', 'SZ']:
                df = df[df['market'] == market]
            
            stocks = df.to_dict('records')
            self.logger.info(f"从CSV获取到 {len(stocks)} 只股票")
            return stocks
            
        except Exception as e:
            self.logger.error(f"读取股票列表失败: {e}")
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
        
        if period != 'daily':
            self.logger.warning(f"CSV数据源仅支持日线数据，不支持: {period}")
            return []
        
        try:
            csv_file = self._get_stock_csv_file(code)
            
            if not csv_file.exists():
                # 尝试生成示例数据
                self._generate_sample_stock_data(code, csv_file)
            
            if not csv_file.exists():
                self.logger.warning(f"股票数据文件不存在: {csv_file}")
                return []
            
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # 转换日期列
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # 筛选日期范围
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 按日期排序
            df = df.sort_values('date')
            
            # 转换为字典列表
            data = []
            for _, row in df.iterrows():
                data.append({
                    'code': code,
                    'date': row['date'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'amount': float(row['amount']) if pd.notna(row['amount']) else 0.0,
                    'change': float(row.get('change', 0)) if pd.notna(row.get('change')) else 0.0,
                    'change_pct': float(row.get('change_pct', 0)) if pd.notna(row.get('change_pct')) else 0.0
                })
            
            self.logger.info(f"从CSV获取到股票 {code} {len(data)} 条数据")
            return data
            
        except Exception as e:
            self.logger.error(f"读取股票数据失败 {code}: {e}")
            return []
    
    def _generate_sample_stock_data(self, code: str, csv_file: Path):
        """生成示例股票数据
        
        Args:
            code: 股票代码
            csv_file: CSV文件路径
        """
        try:
            # 生成最近30天的示例数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 生成随机价格数据
            import random
            base_price = random.uniform(10, 50)
            
            data = []
            prev_close = base_price
            
            for date in dates:
                # 跳过周末
                if date.weekday() >= 5:
                    continue
                
                # 生成随机价格变动
                change_pct = random.uniform(-5, 5)
                change = prev_close * change_pct / 100
                close = prev_close + change
                
                # 生成开高低价
                high = close * random.uniform(1.0, 1.05)
                low = close * random.uniform(0.95, 1.0)
                open_price = prev_close * random.uniform(0.98, 1.02)
                
                # 生成成交量和成交额
                volume = random.randint(100000, 10000000)
                amount = volume * close
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': volume,
                    'amount': round(amount, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2)
                })
                
                prev_close = close
            
            # 保存到CSV文件
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            self.logger.info(f"生成示例数据文件: {csv_file}")
            
        except Exception as e:
            self.logger.error(f"生成示例数据失败: {e}")
    
    async def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据"""
        if not self.enabled:
            return {}
        
        try:
            if not self.realtime_data_file.exists():
                self.logger.warning(f"实时数据文件不存在: {self.realtime_data_file}")
                return {}
            
            df = pd.read_csv(self.realtime_data_file, encoding='utf-8')
            
            # 筛选请求的股票代码
            df = df[df['code'].isin(codes)]
            
            realtime_data = {}
            for _, row in df.iterrows():
                code = row['code']
                realtime_data[code] = {
                    'name': row.get('name', ''),
                    'current_price': float(row['current_price']),
                    'change': float(row['change']),
                    'change_pct': float(row['change_pct']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'prev_close': float(row['prev_close']),
                    'volume': int(row['volume']),
                    'amount': float(row['amount']),
                    'update_time': row.get('update_time', datetime.now().isoformat())
                }
            
            self.logger.info(f"从CSV获取到 {len(realtime_data)} 只股票的实时数据")
            return realtime_data
            
        except Exception as e:
            self.logger.error(f"读取实时数据失败: {e}")
            return {}
    
    async def get_fundamental_data(self, code: str) -> Dict[str, Any]:
        """获取基本面数据"""
        if not self.enabled:
            return {}
        
        try:
            csv_file = self._get_fundamental_csv_file(code)
            
            if not csv_file.exists():
                # 生成示例基本面数据
                self._generate_sample_fundamental_data(code, csv_file)
            
            if not csv_file.exists():
                self.logger.warning(f"基本面数据文件不存在: {csv_file}")
                return {}
            
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            if df.empty:
                return {}
            
            # 获取最新数据
            latest = df.iloc[-1]
            
            fundamental_data = {
                'code': code,
                'pe_ratio': float(latest.get('pe_ratio', 0)) if pd.notna(latest.get('pe_ratio')) else None,
                'pb_ratio': float(latest.get('pb_ratio', 0)) if pd.notna(latest.get('pb_ratio')) else None,
                'market_cap': float(latest.get('market_cap', 0)) if pd.notna(latest.get('market_cap')) else None,
                'total_share': float(latest.get('total_share', 0)) if pd.notna(latest.get('total_share')) else None,
                'float_share': float(latest.get('float_share', 0)) if pd.notna(latest.get('float_share')) else None,
                'revenue': float(latest.get('revenue', 0)) if pd.notna(latest.get('revenue')) else None,
                'net_profit': float(latest.get('net_profit', 0)) if pd.notna(latest.get('net_profit')) else None,
                'roe': float(latest.get('roe', 0)) if pd.notna(latest.get('roe')) else None,
                'debt_ratio': float(latest.get('debt_ratio', 0)) if pd.notna(latest.get('debt_ratio')) else None,
                'update_time': latest.get('update_time', datetime.now().isoformat())
            }
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"读取基本面数据失败 {code}: {e}")
            return {}
    
    def _generate_sample_fundamental_data(self, code: str, csv_file: Path):
        """生成示例基本面数据"""
        try:
            import random
            
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'pe_ratio': round(random.uniform(10, 50), 2),
                'pb_ratio': round(random.uniform(1, 5), 2),
                'market_cap': round(random.uniform(100, 10000), 2),
                'total_share': round(random.uniform(1000, 100000), 2),
                'float_share': round(random.uniform(800, 80000), 2),
                'revenue': round(random.uniform(1000, 100000), 2),
                'net_profit': round(random.uniform(100, 10000), 2),
                'roe': round(random.uniform(5, 25), 2),
                'debt_ratio': round(random.uniform(20, 80), 2),
                'update_time': datetime.now().isoformat()
            }
            
            df = pd.DataFrame([data])
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            self.logger.info(f"生成示例基本面数据: {csv_file}")
            
        except Exception as e:
            self.logger.error(f"生成示例基本面数据失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.enabled:
            return False
        
        try:
            # 检查数据目录是否存在
            if not self.data_dir.exists():
                return False
            
            # 尝试读取股票列表
            stock_list = await self.get_stock_list()
            return len(stock_list) > 0
            
        except Exception as e:
            self.logger.error(f"CSV数据源健康检查失败: {e}")
            return False
    
    def save_stock_data(self, code: str, data: List[Dict[str, Any]]) -> bool:
        """保存股票数据到CSV文件
        
        Args:
            code: 股票代码
            data: 股票数据列表
            
        Returns:
            是否保存成功
        """
        try:
            csv_file = self._get_stock_csv_file(code)
            
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            self.logger.info(f"保存股票数据到CSV: {csv_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存股票数据失败 {code}: {e}")
            return False
    
    def save_realtime_data(self, data: Dict[str, Dict[str, Any]]) -> bool:
        """保存实时数据到CSV文件
        
        Args:
            data: 实时数据字典
            
        Returns:
            是否保存成功
        """
        try:
            # 转换为DataFrame格式
            rows = []
            for code, stock_data in data.items():
                row = {'code': code}
                row.update(stock_data)
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(self.realtime_data_file, index=False, encoding='utf-8')
            
            self.logger.info(f"保存实时数据到CSV: {self.realtime_data_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存实时数据失败: {e}")
            return False