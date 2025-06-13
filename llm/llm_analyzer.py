import openai
import json
import time
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class LLMAnalyzer:
    """大模型新闻分析器"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        """
        初始化LLM分析器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
            base_url: API基础URL（可选，用于使用其他兼容的API服务）
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        
        # 配置OpenAI客户端
        if base_url:
            openai.api_base = base_url
        openai.api_key = api_key
        
        # 分析提示词模板
        self.analysis_prompt_template = """
你是一个专业的金融分析师，请分析以下新闻对A股市场的影响。

新闻标题：{title}
新闻内容：{content}
新闻来源：{source}

请从以下几个维度进行分析：

1. 市场影响力评估（1-10分）：
   - 评估这条新闻对整体A股市场的影响程度
   - 1分表示几乎无影响，10分表示重大影响

2. 情绪倾向分析：
   - 正面(positive)：利好消息，可能推动股价上涨
   - 负面(negative)：利空消息，可能导致股价下跌
   - 中性(neutral)：中性消息，影响不明确

3. 影响板块识别：
   - 列出可能受到影响的主要行业板块
   - 如：科技、金融、医药、消费、地产等

4. 影响时效性：
   - 短期(short)：1-3个交易日
   - 中期(medium)：1-4周
   - 长期(long)：1个月以上

5. 关键词提取：
   - 提取3-5个最重要的关键词

请以JSON格式返回分析结果：
{
  "market_impact_score": 影响力评分(1-10),
  "sentiment": "情绪倾向(positive/negative/neutral)",
  "affected_sectors": ["受影响板块列表"],
  "time_horizon": "影响时效性(short/medium/long)",
  "keywords": ["关键词列表"],
  "analysis_summary": "简要分析总结(50字以内)"
}
"""
        
    def analyze_single_news(self, news_item: Dict) -> Dict:
        """
        分析单条新闻
        
        Args:
            news_item: 新闻数据字典
            
        Returns:
            包含分析结果的字典
        """
        try:
            # 构建分析提示词
            prompt = self.analysis_prompt_template.format(
                title=news_item.get('title', ''),
                content=news_item.get('content', '')[:1000],  # 限制内容长度
                source=news_item.get('source', '')
            )
            
            # 调用大模型API
            response = self._call_llm_api(prompt)
            
            if response:
                # 解析JSON响应
                analysis_result = self._parse_llm_response(response)
                
                # 添加原始新闻信息
                analysis_result.update({
                    'original_news': news_item,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'model_used': self.model
                })
                
                return analysis_result
            else:
                return self._create_fallback_analysis(news_item)
                
        except Exception as e:
            self.logger.error(f"分析新闻时出错: {e}")
            return self._create_fallback_analysis(news_item)
    
    def analyze_news_batch(self, news_list: List[Dict], max_workers: int = 3) -> List[Dict]:
        """
        批量分析新闻
        
        Args:
            news_list: 新闻列表
            max_workers: 最大并发数
            
        Returns:
            分析结果列表
        """
        analysis_results = []
        
        # 使用线程池进行并发分析
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_news = {
                executor.submit(self.analyze_single_news, news): news 
                for news in news_list
            }
            
            # 收集结果
            for future in as_completed(future_to_news):
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    analysis_results.append(result)
                    
                    # 添加延时避免API限制
                    time.sleep(0.5)
                    
                except Exception as e:
                    news = future_to_news[future]
                    self.logger.error(f"分析新闻失败: {news.get('title', '')}, 错误: {e}")
                    analysis_results.append(self._create_fallback_analysis(news))
        
        return analysis_results
    
    def analyze_daily_news(self, daily_news: List[Dict]) -> Dict:
        """
        分析单日新闻并生成汇总报告
        
        Args:
            daily_news: 单日新闻列表
            
        Returns:
            包含分析结果和汇总的字典
        """
        # 分析所有新闻
        analysis_results = self.analyze_news_batch(daily_news)
        
        # 生成汇总报告
        summary = self._generate_daily_summary(analysis_results)
        
        return {
            'date': daily_news[0].get('date', '') if daily_news else '',
            'total_news_count': len(daily_news),
            'analyzed_count': len(analysis_results),
            'individual_analysis': analysis_results,
            'daily_summary': summary
        }
    
    def _call_llm_api(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        调用大模型API
        
        Args:
            prompt: 输入提示词
            max_retries: 最大重试次数
            
        Returns:
            API响应文本
        """
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的金融分析师，擅长分析新闻对股市的影响。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                    timeout=30
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                self.logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"API调用最终失败: {e}")
                    
        return None
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析大模型响应
        
        Args:
            response: 大模型响应文本
            
        Returns:
            解析后的字典
        """
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ['market_impact_score', 'sentiment', 'affected_sectors']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"缺少必要字段: {field}")
                
                # 数据类型验证和修正
                result['market_impact_score'] = max(1, min(10, int(result.get('market_impact_score', 5))))
                result['sentiment'] = str(result.get('sentiment', 'neutral')).lower()
                result['affected_sectors'] = result.get('affected_sectors', [])
                result['time_horizon'] = str(result.get('time_horizon', 'medium')).lower()
                result['keywords'] = result.get('keywords', [])
                result['analysis_summary'] = str(result.get('analysis_summary', ''))[:100]
                
                return result
                
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {e}")
            
        # 如果解析失败，返回默认结果
        return {
            'market_impact_score': 5,
            'sentiment': 'neutral',
            'affected_sectors': [],
            'time_horizon': 'medium',
            'keywords': [],
            'analysis_summary': '解析失败，使用默认分析结果'
        }
    
    def _create_fallback_analysis(self, news_item: Dict) -> Dict:
        """
        创建备用分析结果（当API调用失败时使用）
        
        Args:
            news_item: 新闻数据
            
        Returns:
            备用分析结果
        """
        # 基于关键词的简单分析
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        text = f"{title} {content}".lower()
        
        # 情绪分析
        positive_keywords = ['上涨', '利好', '增长', '盈利', '突破', '创新', '合作', '收购']
        negative_keywords = ['下跌', '利空', '亏损', '风险', '下滑', '减少', '暂停', '调查']
        
        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            impact_score = min(8, 5 + positive_count)
        elif negative_count > positive_count:
            sentiment = 'negative'
            impact_score = min(8, 5 + negative_count)
        else:
            sentiment = 'neutral'
            impact_score = 5
        
        # 板块识别
        sector_keywords = {
            '科技': ['科技', '互联网', '人工智能', 'AI', '芯片', '半导体'],
            '金融': ['银行', '保险', '证券', '基金', '金融'],
            '医药': ['医药', '生物', '疫苗', '药品', '医疗'],
            '消费': ['消费', '零售', '食品', '饮料', '服装'],
            '地产': ['地产', '房地产', '建筑', '基建']
        }
        
        affected_sectors = []
        for sector, keywords in sector_keywords.items():
            if any(kw in text for kw in keywords):
                affected_sectors.append(sector)
        
        return {
            'market_impact_score': impact_score,
            'sentiment': sentiment,
            'affected_sectors': affected_sectors,
            'time_horizon': 'medium',
            'keywords': [],
            'analysis_summary': '基于关键词的简单分析结果',
            'original_news': news_item,
            'analysis_timestamp': datetime.now().isoformat(),
            'model_used': 'fallback_analysis'
        }
    
    def _generate_daily_summary(self, analysis_results: List[Dict]) -> Dict:
        """
        生成每日汇总报告
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            汇总报告字典
        """
        if not analysis_results:
            return {}
        
        # 统计情绪分布
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        impact_scores = []
        all_sectors = []
        
        for result in analysis_results:
            sentiment = result.get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1
            
            impact_score = result.get('market_impact_score', 5)
            impact_scores.append(impact_score)
            
            sectors = result.get('affected_sectors', [])
            all_sectors.extend(sectors)
        
        # 计算平均影响力
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 5
        
        # 统计最受关注的板块
        sector_counts = {}
        for sector in all_sectors:
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        top_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 整体市场情绪
        total_news = len(analysis_results)
        positive_ratio = sentiment_counts['positive'] / total_news
        negative_ratio = sentiment_counts['negative'] / total_news
        
        if positive_ratio > negative_ratio + 0.1:
            overall_sentiment = 'positive'
        elif negative_ratio > positive_ratio + 0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_distribution': sentiment_counts,
            'average_impact_score': round(avg_impact, 2),
            'top_affected_sectors': [sector for sector, count in top_sectors],
            'high_impact_news_count': len([s for s in impact_scores if s >= 7]),
            'summary_timestamp': datetime.now().isoformat()
        }
    
    def batch_analyze_by_date(self, news_by_date: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """
        按日期批量分析新闻
        
        Args:
            news_by_date: 按日期组织的新闻数据
            
        Returns:
            按日期组织的分析结果
        """
        analysis_by_date = {}
        
        for date, daily_news in news_by_date.items():
            self.logger.info(f"正在分析 {date} 的新闻...")
            
            if daily_news:
                analysis_result = self.analyze_daily_news(daily_news)
                analysis_by_date[date] = analysis_result
            else:
                analysis_by_date[date] = {
                    'date': date,
                    'total_news_count': 0,
                    'analyzed_count': 0,
                    'individual_analysis': [],
                    'daily_summary': {}
                }
        
        return analysis_by_date
    
    def save_analysis_results(self, analysis_results: Dict, output_path: str):
        """
        保存分析结果到文件
        
        Args:
            analysis_results: 分析结果数据
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"分析结果已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")