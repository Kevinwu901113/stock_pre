#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐理由解释器
使用AI生成股票推荐的详细解释
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from .ai_interface import AIInterface, AIRequest, AIResponse
from ..core.exceptions import BaseStockException
from ..models.recommendation import Recommendation
from ..models.stock import StockData


@dataclass
class ExplanationContext:
    """解释上下文数据"""
    stock_data: StockData
    recommendation: Recommendation
    market_context: Optional[Dict[str, Any]] = None
    technical_indicators: Optional[Dict[str, Any]] = None
    fundamental_data: Optional[Dict[str, Any]] = None
    news_sentiment: Optional[Dict[str, Any]] = None


@dataclass
class ExplanationResult:
    """解释结果"""
    summary: str  # 简要说明
    detailed_explanation: str  # 详细解释
    key_factors: List[str]  # 关键因素
    risk_warnings: List[str]  # 风险提示
    confidence_score: float  # 置信度
    technical_analysis: Optional[str] = None  # 技术分析
    fundamental_analysis: Optional[str] = None  # 基本面分析
    market_sentiment: Optional[str] = None  # 市场情绪
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RecommendationExplainer:
    """推荐理由解释器"""
    
    def __init__(self, ai_provider: AIInterface):
        self.ai_provider = ai_provider
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """加载提示模板"""
        return {
            "buy_recommendation": """
请分析以下股票的买入推荐理由：

股票信息：
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 当前价格：{current_price}元
- 推荐评分：{score}
- 推荐策略：{strategy_name}

技术指标：
{technical_indicators}

基本面数据：
{fundamental_data}

市场环境：
{market_context}

请从以下几个方面进行分析：
1. 技术面分析（价格趋势、成交量、技术指标等）
2. 基本面分析（财务状况、行业地位、成长性等）
3. 市场情绪和资金流向
4. 风险提示和注意事项

请用专业但易懂的语言解释推荐理由，并给出具体的操作建议。
""",
            
            "sell_recommendation": """
请分析以下股票的卖出推荐理由：

股票信息：
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 当前价格：{current_price}元
- 买入价格：{buy_price}元
- 收益率：{return_rate}%
- 推荐策略：{strategy_name}

技术指标：
{technical_indicators}

持仓情况：
{position_info}

市场环境：
{market_context}

请从以下几个方面进行分析：
1. 止盈/止损分析
2. 技术面变化
3. 市场风险评估
4. 最佳卖出时机

请给出明确的卖出建议和操作要点。
""",
            
            "risk_assessment": """
请对以下股票投资进行风险评估：

股票信息：
{stock_info}

市场数据：
{market_data}

请评估以下风险：
1. 技术风险（价格波动、技术指标风险）
2. 基本面风险（财务风险、行业风险）
3. 市场风险（系统性风险、流动性风险）
4. 政策风险（监管变化、政策影响）

请给出风险等级（低/中/高）和具体的风险控制建议。
"""
        }
    
    async def explain_recommendation(self, context: ExplanationContext) -> ExplanationResult:
        """解释推荐理由"""
        try:
            logger.info(f"开始生成推荐解释: {context.stock_data.code}")
            
            # 选择合适的模板
            template_key = "buy_recommendation" if context.recommendation.action == "buy" else "sell_recommendation"
            template = self.templates.get(template_key, self.templates["buy_recommendation"])
            
            # 构建提示内容
            prompt = self._build_prompt(template, context)
            
            # 调用AI生成解释
            ai_request = AIRequest(
                prompt=prompt,
                context={
                    "stock_code": context.stock_data.code,
                    "action": context.recommendation.action,
                    "strategy": context.recommendation.strategy_name
                },
                parameters={
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            ai_response = await self.ai_provider.generate_text(ai_request)
            
            # 解析AI响应
            explanation_result = self._parse_ai_response(ai_response, context)
            
            logger.info(f"推荐解释生成完成: {context.stock_data.code}")
            return explanation_result
            
        except Exception as e:
            logger.error(f"生成推荐解释失败: {str(e)}")
            # 返回默认解释
            return self._generate_fallback_explanation(context)
    
    def _build_prompt(self, template: str, context: ExplanationContext) -> str:
        """构建AI提示"""
        # 格式化技术指标
        technical_indicators = self._format_technical_indicators(context.technical_indicators)
        
        # 格式化基本面数据
        fundamental_data = self._format_fundamental_data(context.fundamental_data)
        
        # 格式化市场环境
        market_context = self._format_market_context(context.market_context)
        
        # 填充模板
        prompt = template.format(
            stock_code=context.stock_data.code,
            stock_name=context.stock_data.name,
            current_price=context.stock_data.current_price,
            score=context.recommendation.score,
            strategy_name=context.recommendation.strategy_name,
            technical_indicators=technical_indicators,
            fundamental_data=fundamental_data,
            market_context=market_context,
            buy_price=getattr(context.recommendation, 'buy_price', 'N/A'),
            return_rate=getattr(context.recommendation, 'return_rate', 'N/A')
        )
        
        return prompt
    
    def _format_technical_indicators(self, indicators: Optional[Dict[str, Any]]) -> str:
        """格式化技术指标"""
        if not indicators:
            return "暂无技术指标数据"
        
        formatted = []
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {key}: {value:.2f}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_fundamental_data(self, data: Optional[Dict[str, Any]]) -> str:
        """格式化基本面数据"""
        if not data:
            return "暂无基本面数据"
        
        formatted = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {key}: {value:.2f}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_market_context(self, context: Optional[Dict[str, Any]]) -> str:
        """格式化市场环境"""
        if not context:
            return "暂无市场环境数据"
        
        formatted = []
        for key, value in context.items():
            formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _parse_ai_response(self, ai_response: AIResponse, context: ExplanationContext) -> ExplanationResult:
        """解析AI响应"""
        content = ai_response.content
        
        # 简单的文本解析（实际应用中可能需要更复杂的解析逻辑）
        lines = content.split('\n')
        
        summary = ""
        detailed_explanation = content
        key_factors = []
        risk_warnings = []
        
        # 尝试提取关键信息
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "总结" in line or "摘要" in line:
                current_section = "summary"
            elif "关键因素" in line or "主要因素" in line:
                current_section = "factors"
            elif "风险" in line or "注意" in line:
                current_section = "risks"
            elif line.startswith("-") or line.startswith("•"):
                if current_section == "factors":
                    key_factors.append(line[1:].strip())
                elif current_section == "risks":
                    risk_warnings.append(line[1:].strip())
            elif current_section == "summary" and not summary:
                summary = line
        
        # 如果没有提取到摘要，使用前100个字符
        if not summary:
            summary = content[:100] + "..." if len(content) > 100 else content
        
        return ExplanationResult(
            summary=summary,
            detailed_explanation=detailed_explanation,
            key_factors=key_factors or ["技术面向好", "成交量放大"],
            risk_warnings=risk_warnings or ["注意控制仓位", "设置止损位"],
            confidence_score=ai_response.confidence or 0.8,
            technical_analysis=self._extract_section(content, "技术"),
            fundamental_analysis=self._extract_section(content, "基本面"),
            market_sentiment=self._extract_section(content, "市场")
        )
    
    def _extract_section(self, content: str, section_keyword: str) -> Optional[str]:
        """提取特定章节内容"""
        lines = content.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if section_keyword in line and ("分析" in line or "面" in line):
                in_section = True
                continue
            elif in_section and line.strip() and not line.startswith(" "):
                # 遇到新的章节标题，结束当前章节
                if any(keyword in line for keyword in ["基本面", "技术", "市场", "风险"]):
                    break
            
            if in_section and line.strip():
                section_lines.append(line.strip())
        
        return "\n".join(section_lines) if section_lines else None
    
    def _generate_fallback_explanation(self, context: ExplanationContext) -> ExplanationResult:
        """生成备用解释（当AI不可用时）"""
        action = context.recommendation.action
        stock_name = context.stock_data.name
        strategy_name = context.recommendation.strategy_name
        
        if action == "buy":
            summary = f"基于{strategy_name}策略，{stock_name}符合买入条件"
            detailed_explanation = f"""
根据{strategy_name}策略分析，{stock_name}当前呈现以下特征：

1. 技术面分析：
   - 价格走势符合策略要求
   - 成交量配合良好
   - 技术指标发出买入信号

2. 风险提示：
   - 请注意控制仓位
   - 建议设置止损位
   - 关注市场整体走势

建议：可适量关注，注意风险控制。
"""
            key_factors = ["技术指标向好", "成交量放大", "符合策略条件"]
            risk_warnings = ["控制仓位", "设置止损", "关注大盘"]
        else:
            summary = f"基于{strategy_name}策略，建议卖出{stock_name}"
            detailed_explanation = f"""
根据{strategy_name}策略分析，{stock_name}当前建议卖出：

1. 卖出理由：
   - 达到止盈/止损条件
   - 技术面出现转弱信号
   - 策略信号提示卖出

2. 操作建议：
   - 及时止盈保护收益
   - 避免更大损失
   - 等待更好机会

建议：按策略执行卖出操作。
"""
            key_factors = ["达到卖出条件", "保护收益", "控制风险"]
            risk_warnings = ["及时执行", "不要犹豫", "保护本金"]
        
        return ExplanationResult(
            summary=summary,
            detailed_explanation=detailed_explanation,
            key_factors=key_factors,
            risk_warnings=risk_warnings,
            confidence_score=0.6  # 备用解释置信度较低
        )
    
    async def batch_explain_recommendations(self, contexts: List[ExplanationContext]) -> List[ExplanationResult]:
        """批量生成推荐解释"""
        results = []
        
        for context in contexts:
            try:
                result = await self.explain_recommendation(context)
                results.append(result)
            except Exception as e:
                logger.error(f"批量解释失败 {context.stock_data.code}: {str(e)}")
                # 添加备用解释
                fallback = self._generate_fallback_explanation(context)
                results.append(fallback)
        
        return results
    
    async def explain_risk_assessment(self, context: ExplanationContext) -> Dict[str, Any]:
        """生成风险评估解释"""
        try:
            template = self.templates["risk_assessment"]
            
            prompt = template.format(
                stock_info=f"{context.stock_data.code} {context.stock_data.name}",
                market_data=self._format_market_context(context.market_context)
            )
            
            ai_request = AIRequest(
                prompt=prompt,
                parameters={"max_tokens": 500, "temperature": 0.5}
            )
            
            ai_response = await self.ai_provider.generate_text(ai_request)
            
            return {
                "risk_level": "中等",  # 可以从AI响应中解析
                "risk_factors": ["市场波动", "行业风险"],
                "risk_explanation": ai_response.content,
                "risk_control_suggestions": ["控制仓位", "设置止损"],
                "confidence": ai_response.confidence or 0.7
            }
            
        except Exception as e:
            logger.error(f"风险评估解释生成失败: {str(e)}")
            return {
                "risk_level": "中等",
                "risk_factors": ["技术风险", "市场风险"],
                "risk_explanation": "请注意控制风险，合理配置仓位。",
                "risk_control_suggestions": ["分散投资", "止损保护"],
                "confidence": 0.5
            }