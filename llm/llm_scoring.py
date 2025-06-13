import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
from sklearn.preprocessing import MinMaxScaler
from collections import defaultdict

class LLMScoring:
    """大模型分析结果评分器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 情绪权重映射
        self.sentiment_weights = {
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0
        }
        
        # 时效性权重映射
        self.time_horizon_weights = {
            'short': 1.0,
            'medium': 0.7,
            'long': 0.4
        }
        
        # 板块权重（可根据市场情况调整）
        self.sector_weights = {
            '科技': 1.2,
            '金融': 1.0,
            '医药': 1.1,
            '消费': 0.9,
            '地产': 0.8,
            '能源': 1.0,
            '工业': 0.9,
            '材料': 0.8,
            '公用事业': 0.7,
            '电信': 0.8
        }
        
        # 新闻源可信度权重
        self.source_weights = {
            '东方财富': 0.9,
            '新浪财经': 0.8,
            '网易财经': 0.8,
            '同花顺': 0.9,
            '证券时报': 1.0,
            '微博热搜': 0.6,
            '默认': 0.7
        }
    
    def calculate_single_news_score(self, analysis_result: Dict) -> Dict:
        """
        计算单条新闻的综合评分
        
        Args:
            analysis_result: 大模型分析结果
            
        Returns:
            包含各种评分的字典
        """
        try:
            # 基础影响力评分 (1-10)
            impact_score = analysis_result.get('market_impact_score', 5)
            
            # 情绪评分 (-1 到 1)
            sentiment = analysis_result.get('sentiment', 'neutral')
            sentiment_score = self.sentiment_weights.get(sentiment, 0.0)
            
            # 时效性权重
            time_horizon = analysis_result.get('time_horizon', 'medium')
            time_weight = self.time_horizon_weights.get(time_horizon, 0.7)
            
            # 板块权重
            affected_sectors = analysis_result.get('affected_sectors', [])
            sector_weight = self._calculate_sector_weight(affected_sectors)
            
            # 新闻源权重
            source = analysis_result.get('original_news', {}).get('source', '默认')
            source_weight = self.source_weights.get(source, 0.7)
            
            # 综合评分计算
            # 基础分数：影响力 * 情绪 * 时效性
            base_score = (impact_score / 10.0) * sentiment_score * time_weight
            
            # 加权综合分数
            weighted_score = base_score * sector_weight * source_weight
            
            # 标准化到 -1 到 1 范围
            normalized_score = np.tanh(weighted_score)
            
            # 置信度评分（基于分析质量）
            confidence_score = self._calculate_confidence_score(analysis_result)
            
            return {
                'impact_score': impact_score,
                'sentiment_score': sentiment_score,
                'time_weight': time_weight,
                'sector_weight': sector_weight,
                'source_weight': source_weight,
                'base_score': round(base_score, 4),
                'weighted_score': round(weighted_score, 4),
                'normalized_score': round(normalized_score, 4),
                'confidence_score': round(confidence_score, 4),
                'final_score': round(normalized_score * confidence_score, 4)
            }
            
        except Exception as e:
            self.logger.error(f"计算新闻评分时出错: {e}")
            return self._create_default_score()
    
    def calculate_daily_scores(self, daily_analysis: Dict) -> Dict:
        """
        计算单日新闻的综合评分
        
        Args:
            daily_analysis: 单日分析结果
            
        Returns:
            包含各种评分指标的字典
        """
        individual_analysis = daily_analysis.get('individual_analysis', [])
        
        if not individual_analysis:
            return self._create_empty_daily_score(daily_analysis.get('date', ''))
        
        # 计算每条新闻的评分
        news_scores = []
        for analysis in individual_analysis:
            score = self.calculate_single_news_score(analysis)
            score['news_title'] = analysis.get('original_news', {}).get('title', '')
            score['news_source'] = analysis.get('original_news', {}).get('source', '')
            news_scores.append(score)
        
        # 计算汇总指标
        final_scores = [score['final_score'] for score in news_scores]
        confidence_scores = [score['confidence_score'] for score in news_scores]
        
        # 整体市场情绪评分
        overall_sentiment_score = np.mean(final_scores) if final_scores else 0.0
        
        # 加权平均评分（按置信度加权）
        if confidence_scores and sum(confidence_scores) > 0:
            weighted_avg_score = np.average(final_scores, weights=confidence_scores)
        else:
            weighted_avg_score = overall_sentiment_score
        
        # 情绪强度（标准差）
        sentiment_volatility = np.std(final_scores) if len(final_scores) > 1 else 0.0
        
        # 正负新闻比例
        positive_count = len([s for s in final_scores if s > 0.1])
        negative_count = len([s for s in final_scores if s < -0.1])
        neutral_count = len(final_scores) - positive_count - negative_count
        
        total_count = len(final_scores)
        positive_ratio = positive_count / total_count if total_count > 0 else 0
        negative_ratio = negative_count / total_count if total_count > 0 else 0
        neutral_ratio = neutral_count / total_count if total_count > 0 else 0
        
        # 高影响力新闻统计
        high_impact_scores = [score for score in news_scores if score['impact_score'] >= 7]
        high_impact_count = len(high_impact_scores)
        
        # 板块评分统计
        sector_scores = self._calculate_sector_scores(individual_analysis)
        
        return {
            'date': daily_analysis.get('date', ''),
            'total_news_count': total_count,
            'overall_sentiment_score': round(overall_sentiment_score, 4),
            'weighted_avg_score': round(weighted_avg_score, 4),
            'sentiment_volatility': round(sentiment_volatility, 4),
            'positive_ratio': round(positive_ratio, 4),
            'negative_ratio': round(negative_ratio, 4),
            'neutral_ratio': round(neutral_ratio, 4),
            'high_impact_count': high_impact_count,
            'sector_scores': sector_scores,
            'individual_scores': news_scores,
            'score_timestamp': datetime.now().isoformat()
        }
    
    def calculate_period_scores(self, analysis_by_date: Dict[str, Dict]) -> Dict:
        """
        计算时间段内的综合评分
        
        Args:
            analysis_by_date: 按日期组织的分析结果
            
        Returns:
            时间段综合评分
        """
        daily_scores = {}
        
        # 计算每日评分
        for date, daily_analysis in analysis_by_date.items():
            daily_score = self.calculate_daily_scores(daily_analysis)
            daily_scores[date] = daily_score
        
        # 计算时间段汇总指标
        period_summary = self._calculate_period_summary(daily_scores)
        
        return {
            'period_start': min(daily_scores.keys()) if daily_scores else '',
            'period_end': max(daily_scores.keys()) if daily_scores else '',
            'daily_scores': daily_scores,
            'period_summary': period_summary
        }
    
    def _calculate_sector_weight(self, affected_sectors: List[str]) -> float:
        """
        计算板块权重
        
        Args:
            affected_sectors: 受影响的板块列表
            
        Returns:
            板块权重
        """
        if not affected_sectors:
            return 1.0
        
        weights = [self.sector_weights.get(sector, 1.0) for sector in affected_sectors]
        return np.mean(weights)
    
    def _calculate_confidence_score(self, analysis_result: Dict) -> float:
        """
        计算分析结果的置信度评分
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            置信度评分 (0-1)
        """
        confidence = 0.5  # 基础置信度
        
        # 基于模型类型调整
        model_used = analysis_result.get('model_used', '')
        if 'gpt-4' in model_used.lower():
            confidence += 0.3
        elif 'gpt-3.5' in model_used.lower():
            confidence += 0.2
        elif 'fallback' in model_used.lower():
            confidence -= 0.2
        
        # 基于分析完整性调整
        required_fields = ['market_impact_score', 'sentiment', 'affected_sectors']
        complete_fields = sum(1 for field in required_fields if analysis_result.get(field))
        completeness_ratio = complete_fields / len(required_fields)
        confidence *= completeness_ratio
        
        # 基于关键词数量调整
        keywords = analysis_result.get('keywords', [])
        if len(keywords) >= 3:
            confidence += 0.1
        
        # 基于分析摘要长度调整
        summary = analysis_result.get('analysis_summary', '')
        if len(summary) > 20:
            confidence += 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def _calculate_sector_scores(self, individual_analysis: List[Dict]) -> Dict[str, float]:
        """
        计算各板块的评分
        
        Args:
            individual_analysis: 个别分析结果列表
            
        Returns:
            板块评分字典
        """
        sector_scores = defaultdict(list)
        
        for analysis in individual_analysis:
            affected_sectors = analysis.get('affected_sectors', [])
            sentiment = analysis.get('sentiment', 'neutral')
            impact_score = analysis.get('market_impact_score', 5)
            
            sentiment_score = self.sentiment_weights.get(sentiment, 0.0)
            weighted_score = (impact_score / 10.0) * sentiment_score
            
            for sector in affected_sectors:
                sector_scores[sector].append(weighted_score)
        
        # 计算每个板块的平均评分
        final_sector_scores = {}
        for sector, scores in sector_scores.items():
            if scores:
                final_sector_scores[sector] = round(np.mean(scores), 4)
        
        return final_sector_scores
    
    def _calculate_period_summary(self, daily_scores: Dict[str, Dict]) -> Dict:
        """
        计算时间段汇总指标
        
        Args:
            daily_scores: 每日评分字典
            
        Returns:
            时间段汇总指标
        """
        if not daily_scores:
            return {}
        
        # 提取各项指标
        sentiment_scores = []
        weighted_scores = []
        volatilities = []
        positive_ratios = []
        negative_ratios = []
        
        for daily_score in daily_scores.values():
            sentiment_scores.append(daily_score.get('overall_sentiment_score', 0))
            weighted_scores.append(daily_score.get('weighted_avg_score', 0))
            volatilities.append(daily_score.get('sentiment_volatility', 0))
            positive_ratios.append(daily_score.get('positive_ratio', 0))
            negative_ratios.append(daily_score.get('negative_ratio', 0))
        
        # 计算汇总统计
        return {
            'avg_sentiment_score': round(np.mean(sentiment_scores), 4),
            'avg_weighted_score': round(np.mean(weighted_scores), 4),
            'avg_volatility': round(np.mean(volatilities), 4),
            'avg_positive_ratio': round(np.mean(positive_ratios), 4),
            'avg_negative_ratio': round(np.mean(negative_ratios), 4),
            'sentiment_trend': self._calculate_trend(sentiment_scores),
            'score_stability': round(1.0 - np.std(weighted_scores), 4),
            'total_trading_days': len(daily_scores)
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """
        计算评分趋势
        
        Args:
            scores: 评分列表
            
        Returns:
            趋势描述
        """
        if len(scores) < 2:
            return 'insufficient_data'
        
        # 简单线性趋势计算
        x = np.arange(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 0.01:
            return 'upward'
        elif slope < -0.01:
            return 'downward'
        else:
            return 'stable'
    
    def _create_default_score(self) -> Dict:
        """
        创建默认评分
        
        Returns:
            默认评分字典
        """
        return {
            'impact_score': 5,
            'sentiment_score': 0.0,
            'time_weight': 0.7,
            'sector_weight': 1.0,
            'source_weight': 0.7,
            'base_score': 0.0,
            'weighted_score': 0.0,
            'normalized_score': 0.0,
            'confidence_score': 0.3,
            'final_score': 0.0
        }
    
    def _create_empty_daily_score(self, date: str) -> Dict:
        """
        创建空的每日评分
        
        Args:
            date: 日期
            
        Returns:
            空的每日评分字典
        """
        return {
            'date': date,
            'total_news_count': 0,
            'overall_sentiment_score': 0.0,
            'weighted_avg_score': 0.0,
            'sentiment_volatility': 0.0,
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 0.0,
            'high_impact_count': 0,
            'sector_scores': {},
            'individual_scores': [],
            'score_timestamp': datetime.now().isoformat()
        }
    
    def export_scores_to_dataframe(self, period_scores: Dict) -> pd.DataFrame:
        """
        将评分结果导出为DataFrame
        
        Args:
            period_scores: 时间段评分结果
            
        Returns:
            包含评分数据的DataFrame
        """
        daily_scores = period_scores.get('daily_scores', {})
        
        if not daily_scores:
            return pd.DataFrame()
        
        # 构建DataFrame数据
        df_data = []
        for date, score_data in daily_scores.items():
            row = {
                'date': date,
                'overall_sentiment_score': score_data.get('overall_sentiment_score', 0),
                'weighted_avg_score': score_data.get('weighted_avg_score', 0),
                'sentiment_volatility': score_data.get('sentiment_volatility', 0),
                'positive_ratio': score_data.get('positive_ratio', 0),
                'negative_ratio': score_data.get('negative_ratio', 0),
                'neutral_ratio': score_data.get('neutral_ratio', 0),
                'high_impact_count': score_data.get('high_impact_count', 0),
                'total_news_count': score_data.get('total_news_count', 0)
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def save_scores_to_file(self, scores_data: Dict, output_path: str):
        """
        保存评分结果到文件
        
        Args:
            scores_data: 评分数据
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"评分结果已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存评分结果失败: {e}")
    
    def get_market_signal(self, daily_score: Dict, threshold: float = 0.1) -> str:
        """
        根据评分生成市场信号
        
        Args:
            daily_score: 每日评分
            threshold: 信号阈值
            
        Returns:
            市场信号 ('buy', 'sell', 'hold')
        """
        weighted_score = daily_score.get('weighted_avg_score', 0)
        confidence = daily_score.get('sentiment_volatility', 1)
        
        # 考虑置信度的信号生成
        if confidence < 0.3:  # 低波动性，信号更可靠
            if weighted_score > threshold:
                return 'buy'
            elif weighted_score < -threshold:
                return 'sell'
        else:  # 高波动性，提高阈值
            if weighted_score > threshold * 1.5:
                return 'buy'
            elif weighted_score < -threshold * 1.5:
                return 'sell'
        
        return 'hold'