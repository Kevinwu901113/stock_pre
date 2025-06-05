"""自然语言处理器

提供文本分析、情感分析、关键词提取等NLP功能。
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime
from loguru import logger

from .model_manager import model_manager
from config.settings import settings


class NLPProcessor:
    """自然语言处理器
    
    提供文本分析、情感分析、关键词提取、文本摘要等功能。
    """
    
    def __init__(self):
        self.enabled = settings.AI_ENABLED
        self.logger = logger.bind(module="ai.nlp_processor")
        
        # 情感词典
        self.positive_words = {
            '上涨', '涨幅', '增长', '利好', '买入', '推荐', '看好', '强势',
            '突破', '放量', '活跃', '机会', '优质', '稳健', '收益', '盈利'
        }
        
        self.negative_words = {
            '下跌', '跌幅', '下降', '利空', '卖出', '看空', '弱势', '破位',
            '缩量', '低迷', '风险', '亏损', '套牢', '暴跌', '崩盘', '危机'
        }
        
        # 股票相关关键词
        self.stock_keywords = {
            '技术指标': ['均线', 'MACD', 'KDJ', 'RSI', '布林带', '成交量', '换手率'],
            '基本面': ['市盈率', '市净率', '净资产', '营收', '利润', '现金流', '负债率'],
            '市场情绪': ['情绪', '恐慌', '贪婪', '观望', '活跃', '冷清', '热点'],
            '行业板块': ['科技', '医药', '金融', '地产', '消费', '能源', '制造'],
            '操作建议': ['买入', '卖出', '持有', '观望', '加仓', '减仓', '止损', '止盈']
        }
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 待分析文本
            
        Returns:
            情感分析结果
        """
        try:
            if not text or not text.strip():
                return self._get_neutral_sentiment()
            
            if not self.enabled:
                return self._analyze_sentiment_rule_based(text)
            
            # 尝试使用AI模型分析
            ai_result = await self._analyze_sentiment_ai(text)
            
            if ai_result:
                return ai_result
            else:
                # 回退到规则分析
                return self._analyze_sentiment_rule_based(text)
                
        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            return self._get_neutral_sentiment()
    
    async def _analyze_sentiment_ai(self, text: str) -> Optional[Dict[str, Any]]:
        """使用AI模型分析情感
        
        Args:
            text: 待分析文本
            
        Returns:
            AI情感分析结果
        """
        try:
            # 获取NLP模型
            model = model_manager.get_model('nlp_model')
            if not model:
                success = await model_manager.load_model('nlp_model', 'nlp')
                if not success:
                    return None
                model = model_manager.get_model('nlp_model')
            
            if not model:
                return None
            
            # 使用AI模型分析情感
            ai_result = await model.analyze_sentiment(text)
            
            return {
                'sentiment': ai_result.get('sentiment', 'neutral'),
                'confidence': ai_result.get('confidence', 0.5),
                'score': ai_result.get('score', 0.0),
                'details': {
                    'positive_score': ai_result.get('positive_score', 0.0),
                    'negative_score': ai_result.get('negative_score', 0.0),
                    'neutral_score': ai_result.get('neutral_score', 0.0)
                },
                'method': 'ai_model',
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"AI情感分析失败: {e}")
            return None
    
    def _analyze_sentiment_rule_based(self, text: str) -> Dict[str, Any]:
        """基于规则的情感分析
        
        Args:
            text: 待分析文本
            
        Returns:
            规则情感分析结果
        """
        try:
            # 清理文本
            cleaned_text = self._clean_text(text)
            
            # 计算情感得分
            positive_count = sum(1 for word in self.positive_words if word in cleaned_text)
            negative_count = sum(1 for word in self.negative_words if word in cleaned_text)
            
            total_words = len(cleaned_text)
            if total_words == 0:
                return self._get_neutral_sentiment()
            
            # 计算得分
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
            neutral_score = 1 - positive_score - negative_score
            
            # 确定情感倾向
            if positive_score > negative_score and positive_score > 0.1:
                sentiment = 'positive'
                score = positive_score - negative_score
                confidence = min(positive_score * 2, 1.0)
            elif negative_score > positive_score and negative_score > 0.1:
                sentiment = 'negative'
                score = negative_score - positive_score
                confidence = min(negative_score * 2, 1.0)
            else:
                sentiment = 'neutral'
                score = 0.0
                confidence = 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'score': score,
                'details': {
                    'positive_score': positive_score,
                    'negative_score': negative_score,
                    'neutral_score': neutral_score,
                    'positive_words_found': positive_count,
                    'negative_words_found': negative_count
                },
                'method': 'rule_based',
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"规则情感分析失败: {e}")
            return self._get_neutral_sentiment()
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
        """提取关键词
        
        Args:
            text: 待分析文本
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        try:
            if not text or not text.strip():
                return []
            
            if not self.enabled:
                return self._extract_keywords_rule_based(text, max_keywords)
            
            # 尝试使用AI模型提取
            ai_keywords = await self._extract_keywords_ai(text, max_keywords)
            
            if ai_keywords:
                return ai_keywords
            else:
                # 回退到规则提取
                return self._extract_keywords_rule_based(text, max_keywords)
                
        except Exception as e:
            self.logger.error(f"关键词提取失败: {e}")
            return []
    
    async def _extract_keywords_ai(self, text: str, max_keywords: int) -> Optional[List[Dict[str, Any]]]:
        """使用AI模型提取关键词
        
        Args:
            text: 待分析文本
            max_keywords: 最大关键词数量
            
        Returns:
            AI提取的关键词
        """
        try:
            # 获取NLP模型
            model = model_manager.get_model('nlp_model')
            if not model:
                return None
            
            # 使用AI模型提取关键词
            keywords = await model.extract_keywords(text)
            
            # 格式化结果
            formatted_keywords = []
            for i, keyword in enumerate(keywords[:max_keywords]):
                formatted_keywords.append({
                    'keyword': keyword,
                    'score': 1.0 - (i * 0.1),  # 简单的得分计算
                    'category': self._categorize_keyword(keyword),
                    'method': 'ai_model'
                })
            
            return formatted_keywords
            
        except Exception as e:
            self.logger.error(f"AI关键词提取失败: {e}")
            return None
    
    def _extract_keywords_rule_based(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """基于规则的关键词提取
        
        Args:
            text: 待分析文本
            max_keywords: 最大关键词数量
            
        Returns:
            规则提取的关键词
        """
        try:
            # 清理文本
            cleaned_text = self._clean_text(text)
            
            # 收集所有相关关键词
            found_keywords = {}
            
            # 遍历所有类别的关键词
            for category, keywords in self.stock_keywords.items():
                for keyword in keywords:
                    if keyword in cleaned_text:
                        count = cleaned_text.count(keyword)
                        if keyword not in found_keywords:
                            found_keywords[keyword] = {
                                'count': count,
                                'category': category,
                                'score': count / len(cleaned_text)
                            }
                        else:
                            found_keywords[keyword]['count'] += count
                            found_keywords[keyword]['score'] += count / len(cleaned_text)
            
            # 添加情感词
            for word in self.positive_words.union(self.negative_words):
                if word in cleaned_text:
                    count = cleaned_text.count(word)
                    category = '正面情感' if word in self.positive_words else '负面情感'
                    
                    if word not in found_keywords:
                        found_keywords[word] = {
                            'count': count,
                            'category': category,
                            'score': count / len(cleaned_text)
                        }
            
            # 排序并格式化结果
            sorted_keywords = sorted(
                found_keywords.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            
            formatted_keywords = []
            for keyword, info in sorted_keywords[:max_keywords]:
                formatted_keywords.append({
                    'keyword': keyword,
                    'score': info['score'],
                    'category': info['category'],
                    'count': info['count'],
                    'method': 'rule_based'
                })
            
            return formatted_keywords
            
        except Exception as e:
            self.logger.error(f"规则关键词提取失败: {e}")
            return []
    
    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        """生成文本摘要
        
        Args:
            text: 待摘要文本
            max_length: 最大摘要长度
            
        Returns:
            文本摘要
        """
        try:
            if not text or not text.strip():
                return ""
            
            if len(text) <= max_length:
                return text
            
            if not self.enabled:
                return self._generate_summary_rule_based(text, max_length)
            
            # 尝试使用AI模型生成摘要
            ai_summary = await self._generate_summary_ai(text, max_length)
            
            if ai_summary:
                return ai_summary
            else:
                # 回退到规则摘要
                return self._generate_summary_rule_based(text, max_length)
                
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return text[:max_length] + "..."
    
    async def _generate_summary_ai(self, text: str, max_length: int) -> Optional[str]:
        """使用AI模型生成摘要
        
        Args:
            text: 待摘要文本
            max_length: 最大摘要长度
            
        Returns:
            AI生成的摘要
        """
        try:
            # 获取NLP模型
            model = model_manager.get_model('nlp_model')
            if not model:
                return None
            
            # 使用AI模型生成摘要
            summary = await model.generate_summary(text)
            
            # 确保摘要长度不超过限制
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"AI生成摘要失败: {e}")
            return None
    
    def _generate_summary_rule_based(self, text: str, max_length: int) -> str:
        """基于规则的摘要生成
        
        Args:
            text: 待摘要文本
            max_length: 最大摘要长度
            
        Returns:
            规则生成的摘要
        """
        try:
            # 简单的摘要策略：提取包含关键词的句子
            sentences = re.split(r'[。！？.!?]', text)
            
            # 计算每个句子的重要性得分
            sentence_scores = []
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                
                score = 0
                
                # 包含股票关键词的句子得分更高
                for category, keywords in self.stock_keywords.items():
                    for keyword in keywords:
                        if keyword in sentence:
                            score += 2
                
                # 包含情感词的句子得分更高
                for word in self.positive_words.union(self.negative_words):
                    if word in sentence:
                        score += 1
                
                # 句子长度适中的得分更高
                if 10 <= len(sentence) <= 50:
                    score += 1
                
                sentence_scores.append((sentence, score))
            
            # 按得分排序
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 选择最重要的句子组成摘要
            summary_sentences = []
            current_length = 0
            
            for sentence, score in sentence_scores:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            if summary_sentences:
                return '。'.join(summary_sentences) + '。'
            else:
                # 如果没有合适的句子，直接截取
                return text[:max_length] + "..."
                
        except Exception as e:
            self.logger.error(f"规则生成摘要失败: {e}")
            return text[:max_length] + "..."
    
    def _clean_text(self, text: str) -> str:
        """清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        try:
            # 移除特殊字符和多余空格
            cleaned = re.sub(r'[\s]+', '', text)
            
            # 移除数字和英文字母（保留中文）
            cleaned = re.sub(r'[a-zA-Z0-9]+', '', cleaned)
            
            # 移除标点符号
            cleaned = re.sub(r'[，。！？；：""''（）【】《》、]', '', cleaned)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"文本清理失败: {e}")
            return text
    
    def _categorize_keyword(self, keyword: str) -> str:
        """对关键词进行分类
        
        Args:
            keyword: 关键词
            
        Returns:
            关键词类别
        """
        for category, keywords in self.stock_keywords.items():
            if keyword in keywords:
                return category
        
        if keyword in self.positive_words:
            return '正面情感'
        elif keyword in self.negative_words:
            return '负面情感'
        else:
            return '其他'
    
    def _get_neutral_sentiment(self) -> Dict[str, Any]:
        """获取中性情感结果
        
        Returns:
            中性情感分析结果
        """
        return {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'score': 0.0,
            'details': {
                'positive_score': 0.0,
                'negative_score': 0.0,
                'neutral_score': 1.0
            },
            'method': 'default',
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def analyze_text_comprehensive(self, text: str) -> Dict[str, Any]:
        """综合文本分析
        
        Args:
            text: 待分析文本
            
        Returns:
            综合分析结果
        """
        try:
            # 并行执行各种分析
            sentiment_result = await self.analyze_sentiment(text)
            keywords = await self.extract_keywords(text)
            summary = await self.generate_summary(text)
            
            return {
                'sentiment': sentiment_result,
                'keywords': keywords,
                'summary': summary,
                'text_length': len(text),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"综合文本分析失败: {e}")
            return {
                'sentiment': self._get_neutral_sentiment(),
                'keywords': [],
                'summary': text[:100] + "..." if len(text) > 100 else text,
                'text_length': len(text),
                'analyzed_at': datetime.now().isoformat()
            }


# 全局NLP处理器实例
nlp_processor = NLPProcessor()