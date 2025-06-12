#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
功能：获取每日所需数据，包括行情、资金流、新闻等
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import requests
from typing import Dict, List, Optional
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} 重试{max_retries}次后仍然失败: {e}")
                        raise e
                    else:
                        logger.warning(f"{func.__name__} 第{attempt + 1}次尝试失败: {e}, {delay}秒后重试...")
                        time.sleep(delay)
            return None
        return wrapper
    return decorator

class DataFetcher:
    """数据获取类"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d')
        
    @retry_on_failure(max_retries=5, delay=3)
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 使用akshare获取完整的A股股票列表
            stock_list = ak.stock_info_a_code_name()
            if not stock_list.empty:
                logger.info(f"获取到{len(stock_list)}只A股股票")
                return stock_list
            else:
                raise Exception("获取到的股票列表为空")
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise e
    
    def get_stock_realtime_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取股票实时行情数据"""
        realtime_data = {}
        
        # 批量获取所有股票数据，避免频繁请求
        logger.info("批量获取实时行情数据...")
        all_stock_data = self._get_all_stocks_data()
        
        if all_stock_data is not None and not all_stock_data.empty:
            for code in stock_codes:
                try:
                    stock_data = all_stock_data[all_stock_data['代码'] == code]
                    
                    if not stock_data.empty:
                        realtime_data[code] = {
                            'name': stock_data['名称'].iloc[0],
                            'price': float(stock_data['最新价'].iloc[0]),
                            'change_pct': float(stock_data['涨跌幅'].iloc[0]),
                            'volume': int(stock_data['成交量'].iloc[0]) if pd.notna(stock_data['成交量'].iloc[0]) else 0,
                            'turnover': float(stock_data['成交额'].iloc[0]) if pd.notna(stock_data['成交额'].iloc[0]) else 0,
                            'amplitude': float(stock_data['振幅'].iloc[0]),
                            'high': float(stock_data['最高'].iloc[0]),
                            'low': float(stock_data['最低'].iloc[0]),
                            'open': float(stock_data['今开'].iloc[0]),
                            'pre_close': float(stock_data['昨收'].iloc[0])
                        }
                    else:
                        logger.warning(f"股票{code}未找到实时数据，跳过")
                        
                except Exception as e:
                    logger.error(f"处理股票{code}实时数据失败: {e}，跳过该股票")
        else:
            logger.error("批量获取实时数据失败")
            raise Exception("无法获取实时股票数据")
                
        logger.info(f"成功获取{len(realtime_data)}只股票的实时数据")
        return realtime_data
    
    @retry_on_failure(max_retries=3, delay=3)
    def _get_all_stocks_data(self) -> pd.DataFrame:
        """获取所有股票数据"""
        return ak.stock_zh_a_spot_em()
    
    @retry_on_failure(max_retries=3, delay=2)
    def get_stock_history_data(self, stock_code: str, period: int = 30) -> pd.DataFrame:
        """获取股票历史数据"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')
        
        # 获取历史行情数据
        hist_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                     start_date=start_date, end_date=end_date)
        
        if not hist_data.empty:
            return hist_data
        else:
            logger.warning(f"股票{stock_code}历史数据为空")
            raise Exception(f"无法获取股票{stock_code}的历史数据")
    

    
    def get_capital_flow_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取资金流向数据"""
        capital_flow_data = {}
        logger.info("获取资金流向数据...")
        
        for code in stock_codes:
            try:
                # 获取真实的资金流向数据
                market = "sh" if code.startswith('6') else "sz"
                flow_data = ak.stock_individual_fund_flow(stock=code, market=market)
                
                if flow_data is not None and not flow_data.empty:
                    latest_data = flow_data.iloc[-1]
                    capital_flow_data[code] = {
                        'main_net_inflow': latest_data.get('主力净流入-净额', 0),
                        'main_net_inflow_pct': latest_data.get('主力净流入-净占比', 0),
                        'super_large_net_inflow': latest_data.get('超大单净流入-净额', 0),
                        'large_net_inflow': latest_data.get('大单净流入-净额', 0),
                        'medium_net_inflow': latest_data.get('中单净流入-净额', 0),
                        'small_net_inflow': latest_data.get('小单净流入-净额', 0)
                    }
                else:
                    logger.warning(f"股票{code}资金流向数据为空，跳过")
                
            except Exception as e:
                logger.warning(f"获取股票{code}资金流向数据失败: {e}，跳过该股票")
                
        logger.info(f"成功获取{len(capital_flow_data)}只股票的资金流向数据")
        return capital_flow_data
    

    
    def get_market_sentiment_data(self) -> Dict[str, float]:
        """获取市场情绪数据"""
        sentiment_data = {}
        
        # 获取涨跌停数据
        try:
            limit_data = ak.stock_zt_pool_em(date=self.today)
            sentiment_data['limit_up_count'] = len(limit_data) if not limit_data.empty else 0
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise e
        
        # 获取市场总体涨跌情况
        try:
            market_data = ak.stock_zh_a_spot_em()
            if not market_data.empty:
                up_count = len(market_data[market_data['涨跌幅'] > 0])
                down_count = len(market_data[market_data['涨跌幅'] < 0])
                total_count = len(market_data)
                
                sentiment_data['up_ratio'] = up_count / total_count if total_count > 0 else 0
                sentiment_data['down_ratio'] = down_count / total_count if total_count > 0 else 0
            else:
                raise Exception("市场数据为空")
        except Exception as e:
            logger.error(f"获取市场涨跌数据失败: {e}")
            raise e
        
        logger.info(f"市场情绪数据: 涨停{sentiment_data['limit_up_count']}只, 上涨比例{sentiment_data['up_ratio']:.2%}")
        return sentiment_data
    
    def get_news_sentiment(self, stock_codes: List[str]) -> Dict[str, float]:
        """获取新闻情绪数据（简化版）"""
        # 这里可以接入新闻API或爬虫获取新闻情绪
        # 暂时返回随机情绪分数作为示例
        news_sentiment = {}
        
        for code in stock_codes:
            # 实际应用中这里应该是真实的新闻情绪分析
            news_sentiment[code] = np.random.uniform(0.3, 0.7)  # 0-1之间的情绪分数
            
        return news_sentiment
    
    def get_all_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取所有需要的数据"""
        logger.info("开始获取所有数据...")
        
        all_data = {}
        
        # 获取实时行情数据
        logger.info("获取实时行情数据...")
        realtime_data = self.get_stock_realtime_data(stock_codes)
        
        # 获取资金流向数据
        logger.info("获取资金流向数据...")
        capital_flow_data = self.get_capital_flow_data(stock_codes)
        
        # 获取市场情绪数据
        logger.info("获取市场情绪数据...")
        market_sentiment = self.get_market_sentiment_data()
        
        # 获取新闻情绪数据
        logger.info("获取新闻情绪数据...")
        news_sentiment = self.get_news_sentiment(stock_codes)
        
        # 只处理有实时数据的股票
        valid_codes = list(realtime_data.keys())
        logger.info(f"有效股票数量: {len(valid_codes)}/{len(stock_codes)}")
        
        # 整合数据
        for code in valid_codes:
            try:
                # 获取历史数据
                hist_data = self.get_stock_history_data(code)
                
                all_data[code] = {
                    'realtime': realtime_data[code],
                    'capital_flow': capital_flow_data.get(code, {}),
                    'news_sentiment': news_sentiment.get(code, 0.5),
                    'market_sentiment': market_sentiment,
                    'history': hist_data
                }
                
            except Exception as e:
                logger.warning(f"获取股票{code}历史数据失败: {e}，跳过该股票")
                continue
        
        logger.info(f"数据获取完成，成功处理{len(all_data)}只股票")
        return all_data

if __name__ == "__main__":
    # 测试代码
    fetcher = DataFetcher()
    stock_list = fetcher.get_stock_list()
    print(f"获取到{len(stock_list)}只股票")
    
    # 测试获取前10只股票的数据
    test_codes = stock_list['code'].head(10).tolist()
    data = fetcher.get_all_data(test_codes)
    print(f"获取到{len(data)}只股票的完整数据")