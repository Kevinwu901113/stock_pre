import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """财经新闻和热点收集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
        
    def collect_daily_news(self, date: str) -> List[Dict]:
        """收集指定日期的所有新闻数据
        
        Args:
            date: 日期字符串，格式为 'YYYY-MM-DD'
            
        Returns:
            包含所有新闻数据的列表
        """
        all_news = []
        
        # 收集财经新闻
        financial_news = self._collect_financial_news(date)
        all_news.extend(financial_news)
        
        # 收集行业热点
        industry_news = self._collect_industry_hotspots(date)
        all_news.extend(industry_news)
        
        # 收集微博热搜
        weibo_trends = self._collect_weibo_trends(date)
        all_news.extend(weibo_trends)
        
        return all_news
    
    def _collect_financial_news(self, date: str) -> List[Dict]:
        """收集财经新闻"""
        news_list = []
        
        try:
            # 东方财富新闻
            eastmoney_news = self._fetch_eastmoney_news(date)
            news_list.extend(eastmoney_news)
            
            # 新浪财经新闻
            sina_news = self._fetch_sina_finance_news(date)
            news_list.extend(sina_news)
            
            # 网易财经新闻
            netease_news = self._fetch_netease_finance_news(date)
            news_list.extend(netease_news)
            
        except Exception as e:
            self.logger.error(f"收集财经新闻时出错: {e}")
            
        return news_list
    
    def _collect_industry_hotspots(self, date: str) -> List[Dict]:
        """收集行业热点"""
        hotspots = []
        
        try:
            # 同花顺行业资讯
            ths_industry = self._fetch_ths_industry_news(date)
            hotspots.extend(ths_industry)
            
            # 证券时报行业新闻
            stcn_industry = self._fetch_stcn_industry_news(date)
            hotspots.extend(stcn_industry)
            
        except Exception as e:
            self.logger.error(f"收集行业热点时出错: {e}")
            
        return hotspots
    
    def _collect_weibo_trends(self, date: str) -> List[Dict]:
        """收集微博热搜"""
        trends = []
        
        try:
            # 微博热搜榜
            weibo_hot = self._fetch_weibo_hot_search(date)
            trends.extend(weibo_hot)
            
        except Exception as e:
            self.logger.error(f"收集微博热搜时出错: {e}")
            
        return trends
    
    def _fetch_eastmoney_news(self, date: str) -> List[Dict]:
        """抓取东方财富新闻"""
        news_list = []
        
        try:
            # 东方财富新闻API
            url = "http://finance.eastmoney.com/news/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('div', class_='news-item')
                
                for item in news_items:
                    title_elem = item.find('a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href', '')
                        
                        # 获取新闻内容
                        content = self._fetch_news_content(link)
                        
                        news_list.append({
                            'source': '东方财富',
                            'type': 'financial_news',
                            'title': title,
                            'content': content,
                            'url': link,
                            'date': date,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.error(f"抓取东方财富新闻失败: {e}")
            
        return news_list
    
    def _fetch_sina_finance_news(self, date: str) -> List[Dict]:
        """抓取新浪财经新闻"""
        news_list = []
        
        try:
            url = "https://finance.sina.com.cn/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('a', href=re.compile(r'/stock/'))
                
                for item in news_items[:20]:  # 限制数量
                    title = item.get_text().strip()
                    link = item.get('href', '')
                    
                    if title and len(title) > 10:
                        content = self._fetch_news_content(link)
                        
                        news_list.append({
                            'source': '新浪财经',
                            'type': 'financial_news',
                            'title': title,
                            'content': content,
                            'url': link,
                            'date': date,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.error(f"抓取新浪财经新闻失败: {e}")
            
        return news_list
    
    def _fetch_netease_finance_news(self, date: str) -> List[Dict]:
        """抓取网易财经新闻"""
        news_list = []
        
        try:
            url = "https://money.163.com/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('a', href=re.compile(r'money\.163\.com'))
                
                for item in news_items[:15]:  # 限制数量
                    title = item.get_text().strip()
                    link = item.get('href', '')
                    
                    if title and len(title) > 10:
                        content = self._fetch_news_content(link)
                        
                        news_list.append({
                            'source': '网易财经',
                            'type': 'financial_news',
                            'title': title,
                            'content': content,
                            'url': link,
                            'date': date,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.error(f"抓取网易财经新闻失败: {e}")
            
        return news_list
    
    def _fetch_ths_industry_news(self, date: str) -> List[Dict]:
        """抓取同花顺行业资讯"""
        news_list = []
        
        try:
            url = "http://news.10jqka.com.cn/today_list/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('div', class_='list-item')
                
                for item in news_items:
                    title_elem = item.find('a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href', '')
                        
                        content = self._fetch_news_content(link)
                        
                        news_list.append({
                            'source': '同花顺',
                            'type': 'industry_hotspot',
                            'title': title,
                            'content': content,
                            'url': link,
                            'date': date,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.error(f"抓取同花顺行业资讯失败: {e}")
            
        return news_list
    
    def _fetch_stcn_industry_news(self, date: str) -> List[Dict]:
        """抓取证券时报行业新闻"""
        news_list = []
        
        try:
            url = "http://www.stcn.com/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('a', href=re.compile(r'stcn\.com'))
                
                for item in news_items[:10]:  # 限制数量
                    title = item.get_text().strip()
                    link = item.get('href', '')
                    
                    if title and len(title) > 10:
                        content = self._fetch_news_content(link)
                        
                        news_list.append({
                            'source': '证券时报',
                            'type': 'industry_hotspot',
                            'title': title,
                            'content': content,
                            'url': link,
                            'date': date,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.error(f"抓取证券时报行业新闻失败: {e}")
            
        return news_list
    
    def _fetch_weibo_hot_search(self, date: str) -> List[Dict]:
        """抓取微博热搜"""
        trends = []
        
        try:
            # 微博热搜API（模拟）
            url = "https://s.weibo.com/top/summary"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                trend_items = soup.find_all('td', class_='td-02')
                
                for item in trend_items[:20]:  # 限制数量
                    trend_elem = item.find('a')
                    if trend_elem:
                        trend_text = trend_elem.get_text().strip()
                        
                        # 过滤财经相关热搜
                        if self._is_finance_related(trend_text):
                            trends.append({
                                'source': '微博热搜',
                                'type': 'weibo_trend',
                                'title': trend_text,
                                'content': trend_text,
                                'url': '',
                                'date': date,
                                'timestamp': datetime.now().isoformat()
                            })
                            
        except Exception as e:
            self.logger.error(f"抓取微博热搜失败: {e}")
            
        return trends
    
    def _fetch_news_content(self, url: str) -> str:
        """获取新闻详细内容"""
        try:
            if not url or not url.startswith('http'):
                return ""
                
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尝试多种内容选择器
                content_selectors = [
                    'div.article-content',
                    'div.content',
                    'div.news-content',
                    'div.article-body',
                    'div.text'
                ]
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        return content_elem.get_text().strip()[:1000]  # 限制长度
                        
                # 如果没有找到特定选择器，尝试获取所有p标签内容
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text().strip() for p in paragraphs[:5]])
                    return content[:1000]
                    
        except Exception as e:
            self.logger.error(f"获取新闻内容失败: {e}")
            
        return ""
    
    def _is_finance_related(self, text: str) -> bool:
        """判断文本是否与财经相关"""
        finance_keywords = [
            '股票', '股市', '基金', '投资', '理财', '银行', '保险',
            '证券', '期货', '债券', '金融', '经济', '财经', '上市',
            'IPO', '并购', '重组', '业绩', '财报', '涨停', '跌停',
            '牛市', '熊市', 'A股', '港股', '美股', '创业板', '科创板'
        ]
        
        return any(keyword in text for keyword in finance_keywords)
    
    def batch_collect_news(self, start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """批量收集指定日期范围内的新闻
        
        Args:
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'
            
        Returns:
            按日期组织的新闻数据字典
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_news_by_date = {}
        current_dt = start_dt
        
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y-%m-%d')
            self.logger.info(f"正在收集 {date_str} 的新闻数据...")
            
            daily_news = self.collect_daily_news(date_str)
            all_news_by_date[date_str] = daily_news
            
            # 添加延时避免被封
            time.sleep(2)
            current_dt += timedelta(days=1)
            
        return all_news_by_date
    
    def save_news_to_file(self, news_data: Dict[str, List[Dict]], output_path: str):
        """保存新闻数据到文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"新闻数据已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存新闻数据失败: {e}")