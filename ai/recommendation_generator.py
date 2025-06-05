"""推荐理由生成器

基于AI模型生成股票推荐的详细理由和分析报告。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from .model_manager import model_manager
from config.settings import settings


class RecommendationGenerator:
    """推荐理由生成器
    
    使用AI模型生成股票推荐的详细理由、风险评估和投资建议。
    """
    
    def __init__(self):
        self.enabled = settings.AI_ENABLED
        self.logger = logger.bind(module="ai.recommendation_generator")
        
        # 推荐模板
        self.templates = {
            'technical': {
                'buy': "基于技术分析，{stock_name}({stock_code})当前技术指标表现良好。{technical_reason}建议{action}，目标价位{target_price}，止损价位{stop_loss}。",
                'sell': "基于技术分析，{stock_name}({stock_code})技术指标显示{technical_reason}建议{action}，预期收益{expected_return}。"
            },
            'fundamental': {
                'buy': "基于基本面分析，{stock_name}({stock_code})基本面数据显示{fundamental_reason}当前估值{valuation_level}，建议{action}。",
                'sell': "基于基本面分析，{stock_name}({stock_code})基本面数据显示{fundamental_reason}建议{action}。"
            },
            'mixed': {
                'buy': "综合技术面和基本面分析，{stock_name}({stock_code}){mixed_reason}建议{action}，风险等级{risk_level}。",
                'sell': "综合技术面和基本面分析，{stock_name}({stock_code}){mixed_reason}建议{action}。"
            }
        }
    
    async def generate_recommendation_reason(
        self,
        stock_data: Dict[str, Any],
        strategy_result: Dict[str, Any],
        analysis_type: str = 'mixed'
    ) -> Dict[str, Any]:
        """生成推荐理由
        
        Args:
            stock_data: 股票数据
            strategy_result: 策略分析结果
            analysis_type: 分析类型 (technical, fundamental, mixed)
            
        Returns:
            推荐理由和详细分析
        """
        try:
            if not self.enabled:
                return self._generate_template_reason(stock_data, strategy_result, analysis_type)
            
            # 尝试使用AI模型生成理由
            ai_reason = await self._generate_ai_reason(stock_data, strategy_result, analysis_type)
            
            if ai_reason:
                return ai_reason
            else:
                # 回退到模板生成
                return self._generate_template_reason(stock_data, strategy_result, analysis_type)
                
        except Exception as e:
            self.logger.error(f"生成推荐理由失败: {e}")
            return self._generate_template_reason(stock_data, strategy_result, analysis_type)
    
    async def _generate_ai_reason(
        self,
        stock_data: Dict[str, Any],
        strategy_result: Dict[str, Any],
        analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """使用AI模型生成推荐理由
        
        Args:
            stock_data: 股票数据
            strategy_result: 策略分析结果
            analysis_type: 分析类型
            
        Returns:
            AI生成的推荐理由
        """
        try:
            # 获取推荐模型
            model = model_manager.get_model('recommendation_model')
            if not model:
                # 尝试加载模型
                success = await model_manager.load_model('recommendation_model', 'recommendation')
                if not success:
                    return None
                model = model_manager.get_model('recommendation_model')
            
            if not model:
                return None
            
            # 准备输入特征
            features = self._prepare_features(stock_data, strategy_result, analysis_type)
            
            # 使用AI模型生成推荐
            ai_result = await model.predict(features)
            
            # 生成详细理由
            detailed_reason = await model.generate_reason(stock_data)
            
            return {
                'reason': detailed_reason,
                'confidence': ai_result.get('confidence', 0.5),
                'risk_level': ai_result.get('risk_level', 'medium'),
                'target_price': self._calculate_target_price(stock_data, ai_result),
                'stop_loss': self._calculate_stop_loss(stock_data, ai_result),
                'expected_return': ai_result.get('expected_return', 0.0),
                'analysis_type': analysis_type,
                'generated_by': 'ai_model',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"AI生成推荐理由失败: {e}")
            return None
    
    def _prepare_features(self, stock_data: Dict[str, Any], strategy_result: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """准备AI模型输入特征
        
        Args:
            stock_data: 股票数据
            strategy_result: 策略结果
            analysis_type: 分析类型
            
        Returns:
            特征字典
        """
        features = {
            'stock_code': stock_data.get('code', ''),
            'stock_name': stock_data.get('name', ''),
            'current_price': stock_data.get('current_price', 0),
            'change_pct': stock_data.get('change_pct', 0),
            'volume': stock_data.get('volume', 0),
            'market_cap': stock_data.get('market_cap', 0),
            'pe_ratio': stock_data.get('pe_ratio', 0),
            'pb_ratio': stock_data.get('pb_ratio', 0),
            'strategy_signal': strategy_result.get('signal', 'hold'),
            'strategy_confidence': strategy_result.get('confidence', 0.5),
            'strategy_reason': strategy_result.get('reason', ''),
            'analysis_type': analysis_type
        }
        
        # 添加技术指标
        if 'technical_indicators' in stock_data:
            features.update(stock_data['technical_indicators'])
        
        # 添加基本面数据
        if 'fundamental_data' in stock_data:
            features.update(stock_data['fundamental_data'])
        
        return features
    
    def _generate_template_reason(
        self,
        stock_data: Dict[str, Any],
        strategy_result: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """使用模板生成推荐理由
        
        Args:
            stock_data: 股票数据
            strategy_result: 策略结果
            analysis_type: 分析类型
            
        Returns:
            模板生成的推荐理由
        """
        try:
            signal = strategy_result.get('signal', 'hold')
            confidence = strategy_result.get('confidence', 0.5)
            
            # 选择模板
            template_type = analysis_type if analysis_type in self.templates else 'mixed'
            action_templates = self.templates[template_type]
            
            if signal in action_templates:
                template = action_templates[signal]
            else:
                template = action_templates.get('buy', "基于分析，建议关注{stock_name}({stock_code})。")
            
            # 准备模板参数
            template_params = {
                'stock_name': stock_data.get('name', '未知'),
                'stock_code': stock_data.get('code', ''),
                'action': self._get_action_text(signal),
                'target_price': self._calculate_target_price(stock_data, strategy_result),
                'stop_loss': self._calculate_stop_loss(stock_data, strategy_result),
                'expected_return': f"{strategy_result.get('expected_return', 0) * 100:.1f}%",
                'risk_level': self._get_risk_level(confidence),
                'valuation_level': self._get_valuation_level(stock_data)
            }
            
            # 生成具体理由
            if analysis_type == 'technical':
                template_params['technical_reason'] = self._generate_technical_reason(stock_data, strategy_result)
            elif analysis_type == 'fundamental':
                template_params['fundamental_reason'] = self._generate_fundamental_reason(stock_data, strategy_result)
            else:
                template_params['mixed_reason'] = self._generate_mixed_reason(stock_data, strategy_result)
            
            # 格式化模板
            reason = template.format(**template_params)
            
            return {
                'reason': reason,
                'confidence': confidence,
                'risk_level': self._get_risk_level(confidence),
                'target_price': template_params['target_price'],
                'stop_loss': template_params['stop_loss'],
                'expected_return': strategy_result.get('expected_return', 0),
                'analysis_type': analysis_type,
                'generated_by': 'template',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"模板生成推荐理由失败: {e}")
            return {
                'reason': f"基于{analysis_type}分析，建议关注{stock_data.get('name', '')}。",
                'confidence': 0.5,
                'risk_level': 'medium',
                'generated_by': 'fallback',
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_technical_reason(self, stock_data: Dict[str, Any], strategy_result: Dict[str, Any]) -> str:
        """生成技术分析理由"""
        reasons = []
        
        # 价格趋势
        change_pct = stock_data.get('change_pct', 0)
        if change_pct > 2:
            reasons.append("股价呈现强势上涨趋势")
        elif change_pct > 0:
            reasons.append("股价温和上涨")
        elif change_pct < -2:
            reasons.append("股价出现调整")
        else:
            reasons.append("股价相对稳定")
        
        # 成交量
        volume = stock_data.get('volume', 0)
        if volume > 1000000:
            reasons.append("成交量放大")
        
        # 策略信号
        strategy_reason = strategy_result.get('reason', '')
        if strategy_reason:
            reasons.append(strategy_reason)
        
        return "，".join(reasons) + "。"
    
    def _generate_fundamental_reason(self, stock_data: Dict[str, Any], strategy_result: Dict[str, Any]) -> str:
        """生成基本面分析理由"""
        reasons = []
        
        # 估值水平
        pe_ratio = stock_data.get('pe_ratio', 0)
        if 0 < pe_ratio < 15:
            reasons.append("市盈率较低，估值合理")
        elif pe_ratio > 30:
            reasons.append("市盈率偏高，需谨慎")
        
        # 市值规模
        market_cap = stock_data.get('market_cap', 0)
        if market_cap > 1000:
            reasons.append("大盘股，流动性好")
        elif market_cap > 100:
            reasons.append("中盘股，成长性较好")
        
        # 策略信号
        strategy_reason = strategy_result.get('reason', '')
        if strategy_reason:
            reasons.append(strategy_reason)
        
        return "，".join(reasons) + "。"
    
    def _generate_mixed_reason(self, stock_data: Dict[str, Any], strategy_result: Dict[str, Any]) -> str:
        """生成综合分析理由"""
        technical_reason = self._generate_technical_reason(stock_data, strategy_result)
        fundamental_reason = self._generate_fundamental_reason(stock_data, strategy_result)
        
        return f"技术面{technical_reason}基本面{fundamental_reason}"
    
    def _get_action_text(self, signal: str) -> str:
        """获取操作建议文本"""
        action_map = {
            'buy': '买入',
            'sell': '卖出',
            'hold': '持有',
            'strong_buy': '强烈买入',
            'strong_sell': '强烈卖出'
        }
        return action_map.get(signal, '关注')
    
    def _get_risk_level(self, confidence: float) -> str:
        """根据置信度获取风险等级"""
        if confidence >= 0.8:
            return 'low'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'high'
    
    def _get_valuation_level(self, stock_data: Dict[str, Any]) -> str:
        """获取估值水平"""
        pe_ratio = stock_data.get('pe_ratio', 0)
        if 0 < pe_ratio < 15:
            return '偏低'
        elif pe_ratio < 25:
            return '合理'
        else:
            return '偏高'
    
    def _calculate_target_price(self, stock_data: Dict[str, Any], result: Dict[str, Any]) -> str:
        """计算目标价位"""
        try:
            current_price = stock_data.get('current_price', 0)
            if current_price <= 0:
                return '待定'
            
            expected_return = result.get('expected_return', 0.1)
            target_price = current_price * (1 + expected_return)
            
            return f"{target_price:.2f}"
            
        except Exception:
            return '待定'
    
    def _calculate_stop_loss(self, stock_data: Dict[str, Any], result: Dict[str, Any]) -> str:
        """计算止损价位"""
        try:
            current_price = stock_data.get('current_price', 0)
            if current_price <= 0:
                return '待定'
            
            # 默认5%止损
            stop_loss_ratio = result.get('stop_loss_ratio', 0.05)
            stop_loss_price = current_price * (1 - stop_loss_ratio)
            
            return f"{stop_loss_price:.2f}"
            
        except Exception:
            return '待定'
    
    async def generate_batch_reasons(
        self,
        recommendations: List[Dict[str, Any]],
        analysis_type: str = 'mixed'
    ) -> List[Dict[str, Any]]:
        """批量生成推荐理由
        
        Args:
            recommendations: 推荐列表
            analysis_type: 分析类型
            
        Returns:
            包含理由的推荐列表
        """
        try:
            enhanced_recommendations = []
            
            for recommendation in recommendations:
                stock_data = recommendation.get('stock_data', {})
                strategy_result = recommendation.get('strategy_result', {})
                
                # 生成推荐理由
                reason_data = await self.generate_recommendation_reason(
                    stock_data, strategy_result, analysis_type
                )
                
                # 合并数据
                enhanced_recommendation = recommendation.copy()
                enhanced_recommendation.update(reason_data)
                
                enhanced_recommendations.append(enhanced_recommendation)
            
            return enhanced_recommendations
            
        except Exception as e:
            self.logger.error(f"批量生成推荐理由失败: {e}")
            return recommendations
    
    async def generate_market_summary(self, market_data: Dict[str, Any]) -> str:
        """生成市场总结
        
        Args:
            market_data: 市场数据
            
        Returns:
            市场总结文本
        """
        try:
            if not self.enabled:
                return self._generate_template_market_summary(market_data)
            
            # 尝试使用NLP模型生成总结
            nlp_model = model_manager.get_model('nlp_model')
            if nlp_model:
                summary = await nlp_model.generate_summary(str(market_data))
                return summary
            
            # 回退到模板生成
            return self._generate_template_market_summary(market_data)
            
        except Exception as e:
            self.logger.error(f"生成市场总结失败: {e}")
            return "市场数据分析中，请稍后查看详细信息。"
    
    def _generate_template_market_summary(self, market_data: Dict[str, Any]) -> str:
        """使用模板生成市场总结"""
        try:
            summary_parts = []
            
            # 市场指数
            if 'indices' in market_data:
                indices = market_data['indices']
                for index_name, index_data in indices.items():
                    change_pct = index_data.get('change_pct', 0)
                    if change_pct > 1:
                        summary_parts.append(f"{index_name}大涨{change_pct:.1f}%")
                    elif change_pct > 0:
                        summary_parts.append(f"{index_name}上涨{change_pct:.1f}%")
                    elif change_pct < -1:
                        summary_parts.append(f"{index_name}下跌{abs(change_pct):.1f}%")
            
            # 市场情绪
            if 'sentiment' in market_data:
                sentiment = market_data['sentiment']
                if sentiment > 0.6:
                    summary_parts.append("市场情绪偏乐观")
                elif sentiment < 0.4:
                    summary_parts.append("市场情绪偏谨慎")
                else:
                    summary_parts.append("市场情绪中性")
            
            if summary_parts:
                return "今日" + "，".join(summary_parts) + "。"
            else:
                return "市场运行平稳，建议关注个股机会。"
                
        except Exception as e:
            self.logger.error(f"模板生成市场总结失败: {e}")
            return "市场数据分析中，请稍后查看详细信息。"


# 全局推荐理由生成器实例
recommendation_generator = RecommendationGenerator()