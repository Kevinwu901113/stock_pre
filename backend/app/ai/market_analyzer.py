#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场分析器
使用AI进行市场趋势和情绪分析
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from loguru import logger
from .ai_interface import AIInterface, AIRequest, AIResponse
from ..core.exceptions import BaseStockException


class MarketTrend(Enum):
    """市场趋势枚举"""
    BULLISH = "bullish"  # 看涨
    BEARISH = "bearish"  # 看跌
    NEUTRAL = "neutral"  # 中性
    VOLATILE = "volatile"  # 震荡


class MarketSentiment(Enum):
    """市场情绪枚举"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class MarketData:
    """市场数据"""
    index_data: Dict[str, Any]  # 指数数据
    sector_data: Dict[str, Any]  # 板块数据
    volume_data: Dict[str, Any]  # 成交量数据
    money_flow: Dict[str, Any]  # 资金流向
    news_headlines: List[str]  # 新闻标题
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MarketAnalysisResult:
    """市场分析结果"""
    overall_trend: MarketTrend
    sentiment: MarketSentiment
    confidence_score: float
    key_insights: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    sector_analysis: Dict[str, Any]
    technical_summary: str
    fundamental_summary: str
    recommendation: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SectorAnalysis:
    """板块分析结果"""
    sector_name: str
    trend: MarketTrend
    strength: float  # 强度 0-1
    key_stocks: List[str]
    analysis: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MarketAnalyzer:
    """市场分析器"""
    
    def __init__(self, ai_provider: AIInterface):
        self.ai_provider = ai_provider
        self.analysis_templates = self._load_analysis_templates()
    
    def _load_analysis_templates(self) -> Dict[str, str]:
        """加载分析模板"""
        return {
            "market_overview": """
请分析当前A股市场的整体状况：

主要指数表现：
{index_performance}

板块轮动情况：
{sector_rotation}

资金流向：
{money_flow}

成交量变化：
{volume_analysis}

重要新闻：
{news_summary}

请从以下角度进行分析：
1. 市场整体趋势判断（看涨/看跌/震荡）
2. 市场情绪评估（乐观/谨慎/悲观）
3. 关键风险因素识别
4. 投资机会挖掘
5. 后市展望和操作建议

请用专业的语言给出分析结论，并提供具体的投资建议。
""",
            
            "sector_analysis": """
请分析以下板块的投资价值：

板块名称：{sector_name}

板块表现：
{sector_performance}

龙头股票：
{leading_stocks}

行业基本面：
{industry_fundamentals}

政策影响：
{policy_impact}

请分析：
1. 板块当前所处周期位置
2. 投资价值和风险评估
3. 重点关注的个股
4. 最佳投资时机判断

请给出明确的投资建议和风险提示。
""",
            
            "sentiment_analysis": """
请分析当前市场情绪：

市场表现：
{market_performance}

投资者行为：
{investor_behavior}

新闻舆情：
{news_sentiment}

技术指标：
{technical_indicators}

请评估：
1. 当前市场情绪状态（恐慌/谨慎/乐观/狂热）
2. 情绪转换的关键信号
3. 情绪对后市的影响
4. 基于情绪的操作策略

请给出情绪分析结论和相应的投资策略建议。
"""
        }
    
    async def analyze_market_overview(self, market_data: MarketData) -> MarketAnalysisResult:
        """分析市场整体概况"""
        try:
            logger.info("开始进行市场整体分析")
            
            # 构建分析提示
            prompt = self._build_market_analysis_prompt(market_data)
            
            # 调用AI分析
            ai_request = AIRequest(
                prompt=prompt,
                context={"analysis_type": "market_overview"},
                parameters={"max_tokens": 1500, "temperature": 0.6}
            )
            
            ai_response = await self.ai_provider.generate_text(ai_request)
            
            # 解析分析结果
            analysis_result = self._parse_market_analysis(ai_response, market_data)
            
            logger.info("市场整体分析完成")
            return analysis_result
            
        except Exception as e:
            logger.error(f"市场分析失败: {str(e)}")
            return self._generate_fallback_market_analysis(market_data)
    
    def _build_market_analysis_prompt(self, market_data: MarketData) -> str:
        """构建市场分析提示"""
        template = self.analysis_templates["market_overview"]
        
        # 格式化各项数据
        index_performance = self._format_index_data(market_data.index_data)
        sector_rotation = self._format_sector_data(market_data.sector_data)
        money_flow = self._format_money_flow(market_data.money_flow)
        volume_analysis = self._format_volume_data(market_data.volume_data)
        news_summary = self._format_news_headlines(market_data.news_headlines)
        
        return template.format(
            index_performance=index_performance,
            sector_rotation=sector_rotation,
            money_flow=money_flow,
            volume_analysis=volume_analysis,
            news_summary=news_summary
        )
    
    def _format_index_data(self, index_data: Dict[str, Any]) -> str:
        """格式化指数数据"""
        if not index_data:
            return "暂无指数数据"
        
        formatted = []
        for index_name, data in index_data.items():
            if isinstance(data, dict):
                change = data.get('change', 0)
                change_pct = data.get('change_pct', 0)
                formatted.append(f"- {index_name}: {change:+.2f} ({change_pct:+.2f}%)")
            else:
                formatted.append(f"- {index_name}: {data}")
        
        return "\n".join(formatted)
    
    def _format_sector_data(self, sector_data: Dict[str, Any]) -> str:
        """格式化板块数据"""
        if not sector_data:
            return "暂无板块数据"
        
        formatted = []
        for sector, data in sector_data.items():
            if isinstance(data, dict):
                change_pct = data.get('change_pct', 0)
                status = "上涨" if change_pct > 0 else "下跌" if change_pct < 0 else "平盘"
                formatted.append(f"- {sector}: {change_pct:+.2f}% ({status})")
            else:
                formatted.append(f"- {sector}: {data}")
        
        return "\n".join(formatted)
    
    def _format_money_flow(self, money_flow: Dict[str, Any]) -> str:
        """格式化资金流向"""
        if not money_flow:
            return "暂无资金流向数据"
        
        formatted = []
        for flow_type, amount in money_flow.items():
            if isinstance(amount, (int, float)):
                formatted.append(f"- {flow_type}: {amount:.2f}亿元")
            else:
                formatted.append(f"- {flow_type}: {amount}")
        
        return "\n".join(formatted)
    
    def _format_volume_data(self, volume_data: Dict[str, Any]) -> str:
        """格式化成交量数据"""
        if not volume_data:
            return "暂无成交量数据"
        
        formatted = []
        for key, value in volume_data.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {key}: {value:.2f}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_news_headlines(self, headlines: List[str]) -> str:
        """格式化新闻标题"""
        if not headlines:
            return "暂无重要新闻"
        
        # 只取前5条新闻
        top_headlines = headlines[:5]
        return "\n".join([f"- {headline}" for headline in top_headlines])
    
    def _parse_market_analysis(self, ai_response: AIResponse, market_data: MarketData) -> MarketAnalysisResult:
        """解析市场分析结果"""
        content = ai_response.content
        
        # 简单的关键词匹配来确定趋势和情绪
        trend = self._extract_market_trend(content)
        sentiment = self._extract_market_sentiment(content)
        
        # 提取关键信息
        key_insights = self._extract_list_items(content, ["关键", "重点", "主要"])
        risk_factors = self._extract_list_items(content, ["风险", "注意", "警惕"])
        opportunities = self._extract_list_items(content, ["机会", "建议", "关注"])
        
        # 提取技术和基本面总结
        technical_summary = self._extract_section(content, "技术")
        fundamental_summary = self._extract_section(content, "基本面")
        
        # 提取投资建议
        recommendation = self._extract_section(content, "建议") or "请根据个人风险承受能力谨慎投资"
        
        return MarketAnalysisResult(
            overall_trend=trend,
            sentiment=sentiment,
            confidence_score=ai_response.confidence or 0.8,
            key_insights=key_insights,
            risk_factors=risk_factors,
            opportunities=opportunities,
            sector_analysis=self._analyze_sectors_from_content(content),
            technical_summary=technical_summary or "技术面整体稳定",
            fundamental_summary=fundamental_summary or "基本面保持健康",
            recommendation=recommendation
        )
    
    def _extract_market_trend(self, content: str) -> MarketTrend:
        """从内容中提取市场趋势"""
        content_lower = content.lower()
        
        bullish_keywords = ["看涨", "上涨", "牛市", "乐观", "向好"]
        bearish_keywords = ["看跌", "下跌", "熊市", "悲观", "走弱"]
        volatile_keywords = ["震荡", "波动", "整理", "盘整"]
        
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in content)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in content)
        volatile_count = sum(1 for keyword in volatile_keywords if keyword in content)
        
        if volatile_count > max(bullish_count, bearish_count):
            return MarketTrend.VOLATILE
        elif bullish_count > bearish_count:
            return MarketTrend.BULLISH
        elif bearish_count > bullish_count:
            return MarketTrend.BEARISH
        else:
            return MarketTrend.NEUTRAL
    
    def _extract_market_sentiment(self, content: str) -> MarketSentiment:
        """从内容中提取市场情绪"""
        positive_keywords = ["乐观", "积极", "看好", "信心"]
        negative_keywords = ["悲观", "谨慎", "担忧", "恐慌"]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in content)
        negative_count = sum(1 for keyword in negative_keywords if keyword in content)
        
        if positive_count > negative_count * 1.5:
            return MarketSentiment.POSITIVE
        elif negative_count > positive_count * 1.5:
            return MarketSentiment.NEGATIVE
        else:
            return MarketSentiment.NEUTRAL
    
    def _extract_list_items(self, content: str, keywords: List[str]) -> List[str]:
        """提取列表项"""
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in keywords):
                # 查找后续的列表项
                continue
            elif line.startswith(('-', '•', '1.', '2.', '3.')):
                items.append(line[2:].strip() if line.startswith(('-', '•')) else line[3:].strip())
        
        return items[:5]  # 最多返回5个项目
    
    def _extract_section(self, content: str, section_keyword: str) -> Optional[str]:
        """提取特定章节内容"""
        lines = content.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if section_keyword in line and ("分析" in line or "面" in line or "建议" in line):
                in_section = True
                continue
            elif in_section and line.strip() and line[0].isdigit():
                # 遇到新的编号章节，结束当前章节
                break
            
            if in_section and line.strip():
                section_lines.append(line.strip())
        
        return "\n".join(section_lines) if section_lines else None
    
    def _analyze_sectors_from_content(self, content: str) -> Dict[str, Any]:
        """从内容中分析板块信息"""
        # 简单的板块分析提取
        sectors = {}
        
        common_sectors = ["科技", "医药", "金融", "地产", "消费", "新能源", "军工"]
        
        for sector in common_sectors:
            if sector in content:
                # 简单的情感分析
                sector_context = self._get_context_around_keyword(content, sector)
                if any(word in sector_context for word in ["看好", "推荐", "机会"]):
                    sectors[sector] = {"trend": "positive", "strength": 0.7}
                elif any(word in sector_context for word in ["谨慎", "风险", "回调"]):
                    sectors[sector] = {"trend": "negative", "strength": 0.3}
                else:
                    sectors[sector] = {"trend": "neutral", "strength": 0.5}
        
        return sectors
    
    def _get_context_around_keyword(self, content: str, keyword: str, window: int = 50) -> str:
        """获取关键词周围的上下文"""
        index = content.find(keyword)
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(content), index + len(keyword) + window)
        
        return content[start:end]
    
    def _generate_fallback_market_analysis(self, market_data: MarketData) -> MarketAnalysisResult:
        """生成备用市场分析"""
        return MarketAnalysisResult(
            overall_trend=MarketTrend.NEUTRAL,
            sentiment=MarketSentiment.NEUTRAL,
            confidence_score=0.5,
            key_insights=["市场处于整理阶段", "关注政策面变化"],
            risk_factors=["外部环境不确定性", "流动性变化风险"],
            opportunities=["结构性机会仍存", "优质个股可关注"],
            sector_analysis={"整体": {"trend": "neutral", "strength": 0.5}},
            technical_summary="技术面整体平稳，等待方向选择",
            fundamental_summary="基本面保持稳定，关注业绩变化",
            recommendation="建议保持谨慎乐观，控制仓位风险"
        )
    
    async def analyze_sector(self, sector_name: str, sector_data: Dict[str, Any]) -> SectorAnalysis:
        """分析特定板块"""
        try:
            logger.info(f"开始分析板块: {sector_name}")
            
            template = self.analysis_templates["sector_analysis"]
            
            prompt = template.format(
                sector_name=sector_name,
                sector_performance=self._format_sector_performance(sector_data),
                leading_stocks=self._format_leading_stocks(sector_data.get('leading_stocks', [])),
                industry_fundamentals=self._format_fundamentals(sector_data.get('fundamentals', {})),
                policy_impact=self._format_policy_impact(sector_data.get('policy', {}))
            )
            
            ai_request = AIRequest(
                prompt=prompt,
                parameters={"max_tokens": 800, "temperature": 0.6}
            )
            
            ai_response = await self.ai_provider.generate_text(ai_request)
            
            # 解析板块分析结果
            trend = self._extract_market_trend(ai_response.content)
            strength = self._calculate_sector_strength(ai_response.content)
            key_stocks = self._extract_key_stocks(ai_response.content)
            
            return SectorAnalysis(
                sector_name=sector_name,
                trend=trend,
                strength=strength,
                key_stocks=key_stocks,
                analysis=ai_response.content
            )
            
        except Exception as e:
            logger.error(f"板块分析失败 {sector_name}: {str(e)}")
            return SectorAnalysis(
                sector_name=sector_name,
                trend=MarketTrend.NEUTRAL,
                strength=0.5,
                key_stocks=[],
                analysis=f"{sector_name}板块整体表现平稳，建议持续关注。"
            )
    
    def _format_sector_performance(self, sector_data: Dict[str, Any]) -> str:
        """格式化板块表现"""
        if not sector_data:
            return "暂无板块表现数据"
        
        performance = sector_data.get('performance', {})
        formatted = []
        
        for period, value in performance.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {period}: {value:+.2f}%")
        
        return "\n".join(formatted) if formatted else "暂无具体表现数据"
    
    def _format_leading_stocks(self, stocks: List[str]) -> str:
        """格式化龙头股票"""
        if not stocks:
            return "暂无龙头股票信息"
        
        return "\n".join([f"- {stock}" for stock in stocks[:5]])
    
    def _format_fundamentals(self, fundamentals: Dict[str, Any]) -> str:
        """格式化基本面数据"""
        if not fundamentals:
            return "暂无基本面数据"
        
        formatted = []
        for key, value in fundamentals.items():
            formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_policy_impact(self, policy: Dict[str, Any]) -> str:
        """格式化政策影响"""
        if not policy:
            return "暂无相关政策信息"
        
        formatted = []
        for key, value in policy.items():
            formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _calculate_sector_strength(self, content: str) -> float:
        """计算板块强度"""
        positive_words = ["强势", "看好", "机会", "推荐", "上涨"]
        negative_words = ["弱势", "谨慎", "风险", "下跌", "回调"]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.5
        
        strength = positive_count / total_count
        return max(0.1, min(0.9, strength))  # 限制在0.1-0.9之间
    
    def _extract_key_stocks(self, content: str) -> List[str]:
        """提取关键股票"""
        # 简单的股票代码匹配（6位数字）
        import re
        stock_codes = re.findall(r'\b\d{6}\b', content)
        return list(set(stock_codes))[:5]  # 去重并限制数量
    
    async def analyze_sentiment(self, market_data: MarketData) -> Dict[str, Any]:
        """分析市场情绪"""
        try:
            template = self.analysis_templates["sentiment_analysis"]
            
            prompt = template.format(
                market_performance=self._format_index_data(market_data.index_data),
                investor_behavior=self._format_volume_data(market_data.volume_data),
                news_sentiment=self._format_news_headlines(market_data.news_headlines),
                technical_indicators="技术指标整体中性"
            )
            
            ai_request = AIRequest(
                prompt=prompt,
                parameters={"max_tokens": 600, "temperature": 0.5}
            )
            
            ai_response = await self.ai_provider.generate_text(ai_request)
            
            sentiment = self._extract_market_sentiment(ai_response.content)
            
            return {
                "sentiment": sentiment.value,
                "confidence": ai_response.confidence or 0.7,
                "analysis": ai_response.content,
                "key_factors": self._extract_list_items(ai_response.content, ["因素", "原因"]),
                "outlook": self._extract_section(ai_response.content, "展望") or "保持关注市场变化"
            }
            
        except Exception as e:
            logger.error(f"情绪分析失败: {str(e)}")
            return {
                "sentiment": MarketSentiment.NEUTRAL.value,
                "confidence": 0.5,
                "analysis": "市场情绪整体保持中性，建议谨慎观察。",
                "key_factors": ["市场波动", "政策影响"],
                "outlook": "短期保持谨慎，中长期关注结构性机会"
            }