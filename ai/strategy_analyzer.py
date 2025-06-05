"""策略分析器

使用AI模型对量化策略进行分析、优化和评估。
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from .model_manager import model_manager
from config.settings import settings


class StrategyAnalyzer:
    """策略分析器
    
    使用AI模型分析策略表现，提供优化建议和风险评估。
    """
    
    def __init__(self):
        self.enabled = settings.AI_ENABLED
        self.logger = logger.bind(module="ai.strategy_analyzer")
        
        # 分析指标权重
        self.metric_weights = {
            'return_rate': 0.3,
            'sharpe_ratio': 0.25,
            'max_drawdown': 0.2,
            'win_rate': 0.15,
            'profit_loss_ratio': 0.1
        }
    
    async def analyze_strategy_performance(
        self,
        strategy_name: str,
        backtest_results: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析策略表现
        
        Args:
            strategy_name: 策略名称
            backtest_results: 回测结果
            market_data: 市场数据
            
        Returns:
            策略分析结果
        """
        try:
            if not self.enabled:
                return self._analyze_strategy_template(strategy_name, backtest_results, market_data)
            
            # 尝试使用AI模型分析
            ai_analysis = await self._analyze_strategy_ai(strategy_name, backtest_results, market_data)
            
            if ai_analysis:
                return ai_analysis
            else:
                # 回退到传统分析
                return self._analyze_strategy_template(strategy_name, backtest_results, market_data)
                
        except Exception as e:
            self.logger.error(f"策略分析失败: {e}")
            return self._get_default_analysis(strategy_name)
    
    async def _analyze_strategy_ai(
        self,
        strategy_name: str,
        backtest_results: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """使用AI模型分析策略
        
        Args:
            strategy_name: 策略名称
            backtest_results: 回测结果
            market_data: 市场数据
            
        Returns:
            AI分析结果
        """
        try:
            # 获取策略分析模型
            model = model_manager.get_model('strategy_model')
            if not model:
                success = await model_manager.load_model('strategy_model', 'strategy')
                if not success:
                    return None
                model = model_manager.get_model('strategy_model')
            
            if not model:
                return None
            
            # 准备分析数据
            analysis_data = self._prepare_analysis_data(strategy_name, backtest_results, market_data)
            
            # 使用AI模型分析
            ai_result = await model.analyze_strategy(analysis_data)
            
            # 获取优化建议
            optimization_suggestions = await model.optimize_parameters(backtest_results.get('parameters', {}))
            
            return {
                'strategy_name': strategy_name,
                'performance_score': ai_result.get('performance_score', 0.5),
                'risk_score': ai_result.get('risk_score', 0.5),
                'overall_rating': self._calculate_overall_rating(ai_result),
                'strengths': ai_result.get('strengths', []),
                'weaknesses': ai_result.get('weaknesses', []),
                'suggestions': ai_result.get('suggestions', []),
                'optimization': optimization_suggestions,
                'market_adaptability': self._assess_market_adaptability(backtest_results, market_data),
                'risk_assessment': self._assess_risk(backtest_results),
                'analysis_type': 'ai_model',
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"AI策略分析失败: {e}")
            return None
    
    def _analyze_strategy_template(
        self,
        strategy_name: str,
        backtest_results: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用传统方法分析策略
        
        Args:
            strategy_name: 策略名称
            backtest_results: 回测结果
            market_data: 市场数据
            
        Returns:
            传统分析结果
        """
        try:
            # 计算基础指标
            metrics = self._calculate_basic_metrics(backtest_results)
            
            # 评估表现
            performance_score = self._calculate_performance_score(metrics)
            risk_score = self._calculate_risk_score(metrics)
            
            # 生成建议
            suggestions = self._generate_suggestions(metrics, backtest_results)
            
            # 评估市场适应性
            market_adaptability = self._assess_market_adaptability(backtest_results, market_data)
            
            return {
                'strategy_name': strategy_name,
                'performance_score': performance_score,
                'risk_score': risk_score,
                'overall_rating': self._calculate_overall_rating({
                    'performance_score': performance_score,
                    'risk_score': risk_score
                }),
                'metrics': metrics,
                'strengths': self._identify_strengths(metrics),
                'weaknesses': self._identify_weaknesses(metrics),
                'suggestions': suggestions,
                'market_adaptability': market_adaptability,
                'risk_assessment': self._assess_risk(backtest_results),
                'analysis_type': 'template',
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"传统策略分析失败: {e}")
            return self._get_default_analysis(strategy_name)
    
    def _prepare_analysis_data(self, strategy_name: str, backtest_results: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备AI分析数据"""
        return {
            'strategy_name': strategy_name,
            'total_return': backtest_results.get('total_return', 0),
            'annual_return': backtest_results.get('annual_return', 0),
            'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
            'max_drawdown': backtest_results.get('max_drawdown', 0),
            'win_rate': backtest_results.get('win_rate', 0),
            'profit_loss_ratio': backtest_results.get('profit_loss_ratio', 0),
            'total_trades': backtest_results.get('total_trades', 0),
            'avg_holding_period': backtest_results.get('avg_holding_period', 0),
            'volatility': backtest_results.get('volatility', 0),
            'market_correlation': backtest_results.get('market_correlation', 0),
            'parameters': backtest_results.get('parameters', {}),
            'market_conditions': market_data
        }
    
    def _calculate_basic_metrics(self, backtest_results: Dict[str, Any]) -> Dict[str, float]:
        """计算基础指标"""
        try:
            returns = backtest_results.get('returns', [])
            if not returns:
                return {}
            
            returns_array = np.array(returns)
            
            metrics = {
                'total_return': backtest_results.get('total_return', 0),
                'annual_return': backtest_results.get('annual_return', 0),
                'volatility': np.std(returns_array) * np.sqrt(252) if len(returns_array) > 1 else 0,
                'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
                'max_drawdown': backtest_results.get('max_drawdown', 0),
                'win_rate': backtest_results.get('win_rate', 0),
                'profit_loss_ratio': backtest_results.get('profit_loss_ratio', 0),
                'total_trades': backtest_results.get('total_trades', 0),
                'avg_holding_period': backtest_results.get('avg_holding_period', 0)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算基础指标失败: {e}")
            return {}
    
    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """计算表现得分"""
        try:
            score = 0.0
            
            # 年化收益率得分 (0-1)
            annual_return = metrics.get('annual_return', 0)
            if annual_return > 0.2:
                score += 0.3
            elif annual_return > 0.1:
                score += 0.2
            elif annual_return > 0.05:
                score += 0.1
            
            # 夏普比率得分 (0-0.25)
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            if sharpe_ratio > 2:
                score += 0.25
            elif sharpe_ratio > 1:
                score += 0.2
            elif sharpe_ratio > 0.5:
                score += 0.15
            elif sharpe_ratio > 0:
                score += 0.1
            
            # 最大回撤得分 (0-0.2)
            max_drawdown = abs(metrics.get('max_drawdown', 0))
            if max_drawdown < 0.05:
                score += 0.2
            elif max_drawdown < 0.1:
                score += 0.15
            elif max_drawdown < 0.2:
                score += 0.1
            elif max_drawdown < 0.3:
                score += 0.05
            
            # 胜率得分 (0-0.15)
            win_rate = metrics.get('win_rate', 0)
            if win_rate > 0.6:
                score += 0.15
            elif win_rate > 0.5:
                score += 0.1
            elif win_rate > 0.4:
                score += 0.05
            
            # 盈亏比得分 (0-0.1)
            profit_loss_ratio = metrics.get('profit_loss_ratio', 0)
            if profit_loss_ratio > 2:
                score += 0.1
            elif profit_loss_ratio > 1.5:
                score += 0.08
            elif profit_loss_ratio > 1:
                score += 0.05
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"计算表现得分失败: {e}")
            return 0.5
    
    def _calculate_risk_score(self, metrics: Dict[str, float]) -> float:
        """计算风险得分 (越低越好)"""
        try:
            risk_score = 0.0
            
            # 波动率风险
            volatility = metrics.get('volatility', 0)
            if volatility > 0.3:
                risk_score += 0.4
            elif volatility > 0.2:
                risk_score += 0.3
            elif volatility > 0.15:
                risk_score += 0.2
            elif volatility > 0.1:
                risk_score += 0.1
            
            # 最大回撤风险
            max_drawdown = abs(metrics.get('max_drawdown', 0))
            if max_drawdown > 0.3:
                risk_score += 0.4
            elif max_drawdown > 0.2:
                risk_score += 0.3
            elif max_drawdown > 0.1:
                risk_score += 0.2
            elif max_drawdown > 0.05:
                risk_score += 0.1
            
            # 夏普比率风险 (夏普比率低表示风险高)
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            if sharpe_ratio < 0:
                risk_score += 0.2
            elif sharpe_ratio < 0.5:
                risk_score += 0.1
            elif sharpe_ratio < 1:
                risk_score += 0.05
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"计算风险得分失败: {e}")
            return 0.5
    
    def _calculate_overall_rating(self, result: Dict[str, float]) -> str:
        """计算总体评级"""
        try:
            performance_score = result.get('performance_score', 0.5)
            risk_score = result.get('risk_score', 0.5)
            
            # 综合得分 (表现得分高，风险得分低为好)
            overall_score = performance_score * 0.7 + (1 - risk_score) * 0.3
            
            if overall_score >= 0.8:
                return 'A'
            elif overall_score >= 0.7:
                return 'B'
            elif overall_score >= 0.6:
                return 'C'
            elif overall_score >= 0.5:
                return 'D'
            else:
                return 'E'
                
        except Exception:
            return 'C'
    
    def _identify_strengths(self, metrics: Dict[str, float]) -> List[str]:
        """识别策略优势"""
        strengths = []
        
        try:
            if metrics.get('annual_return', 0) > 0.15:
                strengths.append('年化收益率较高')
            
            if metrics.get('sharpe_ratio', 0) > 1.5:
                strengths.append('风险调整收益优秀')
            
            if abs(metrics.get('max_drawdown', 0)) < 0.1:
                strengths.append('回撤控制良好')
            
            if metrics.get('win_rate', 0) > 0.6:
                strengths.append('胜率较高')
            
            if metrics.get('profit_loss_ratio', 0) > 1.5:
                strengths.append('盈亏比良好')
            
            if metrics.get('volatility', 0) < 0.15:
                strengths.append('波动率较低')
                
        except Exception as e:
            self.logger.error(f"识别策略优势失败: {e}")
        
        return strengths if strengths else ['策略表现稳定']
    
    def _identify_weaknesses(self, metrics: Dict[str, float]) -> List[str]:
        """识别策略劣势"""
        weaknesses = []
        
        try:
            if metrics.get('annual_return', 0) < 0.05:
                weaknesses.append('年化收益率偏低')
            
            if metrics.get('sharpe_ratio', 0) < 0.5:
                weaknesses.append('风险调整收益不佳')
            
            if abs(metrics.get('max_drawdown', 0)) > 0.2:
                weaknesses.append('最大回撤较大')
            
            if metrics.get('win_rate', 0) < 0.4:
                weaknesses.append('胜率偏低')
            
            if metrics.get('profit_loss_ratio', 0) < 1:
                weaknesses.append('盈亏比不佳')
            
            if metrics.get('volatility', 0) > 0.25:
                weaknesses.append('波动率较高')
                
        except Exception as e:
            self.logger.error(f"识别策略劣势失败: {e}")
        
        return weaknesses
    
    def _generate_suggestions(self, metrics: Dict[str, float], backtest_results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        try:
            # 基于指标生成建议
            if abs(metrics.get('max_drawdown', 0)) > 0.15:
                suggestions.append('建议增加止损条件以控制回撤')
            
            if metrics.get('win_rate', 0) < 0.5:
                suggestions.append('建议优化入场条件以提高胜率')
            
            if metrics.get('profit_loss_ratio', 0) < 1.2:
                suggestions.append('建议调整止盈止损比例')
            
            if metrics.get('sharpe_ratio', 0) < 1:
                suggestions.append('建议优化风险管理策略')
            
            if metrics.get('total_trades', 0) < 50:
                suggestions.append('建议增加交易频率以获得更多样本')
            elif metrics.get('total_trades', 0) > 500:
                suggestions.append('建议减少过度交易')
            
            # 基于参数生成建议
            parameters = backtest_results.get('parameters', {})
            if 'short_period' in parameters and 'long_period' in parameters:
                short_period = parameters['short_period']
                long_period = parameters['long_period']
                if long_period - short_period < 10:
                    suggestions.append('建议增大均线周期差距')
                    
        except Exception as e:
            self.logger.error(f"生成优化建议失败: {e}")
        
        return suggestions if suggestions else ['策略表现良好，建议继续观察']
    
    def _assess_market_adaptability(self, backtest_results: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估市场适应性"""
        try:
            # 分析不同市场环境下的表现
            adaptability = {
                'bull_market': 0.5,
                'bear_market': 0.5,
                'sideways_market': 0.5,
                'high_volatility': 0.5,
                'low_volatility': 0.5,
                'overall_score': 0.5
            }
            
            # 如果有分段回测结果，进行详细分析
            if 'period_analysis' in backtest_results:
                period_analysis = backtest_results['period_analysis']
                
                for period, results in period_analysis.items():
                    market_condition = results.get('market_condition', 'unknown')
                    period_return = results.get('return', 0)
                    
                    if market_condition == 'bull' and period_return > 0.1:
                        adaptability['bull_market'] = 0.8
                    elif market_condition == 'bear' and period_return > -0.05:
                        adaptability['bear_market'] = 0.8
                    elif market_condition == 'sideways' and period_return > 0.05:
                        adaptability['sideways_market'] = 0.8
            
            # 计算总体适应性得分
            adaptability['overall_score'] = np.mean([
                adaptability['bull_market'],
                adaptability['bear_market'],
                adaptability['sideways_market']
            ])
            
            return adaptability
            
        except Exception as e:
            self.logger.error(f"评估市场适应性失败: {e}")
            return {'overall_score': 0.5}
    
    def _assess_risk(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险"""
        try:
            risk_assessment = {
                'market_risk': 'medium',
                'liquidity_risk': 'low',
                'concentration_risk': 'medium',
                'timing_risk': 'medium',
                'overall_risk': 'medium'
            }
            
            # 基于回测结果评估风险
            max_drawdown = abs(backtest_results.get('max_drawdown', 0))
            volatility = backtest_results.get('volatility', 0)
            
            # 市场风险
            if max_drawdown > 0.2 or volatility > 0.25:
                risk_assessment['market_risk'] = 'high'
            elif max_drawdown < 0.1 and volatility < 0.15:
                risk_assessment['market_risk'] = 'low'
            
            # 集中度风险
            total_trades = backtest_results.get('total_trades', 0)
            if total_trades < 30:
                risk_assessment['concentration_risk'] = 'high'
            elif total_trades > 100:
                risk_assessment['concentration_risk'] = 'low'
            
            # 时机风险
            win_rate = backtest_results.get('win_rate', 0)
            if win_rate < 0.4:
                risk_assessment['timing_risk'] = 'high'
            elif win_rate > 0.6:
                risk_assessment['timing_risk'] = 'low'
            
            # 总体风险
            risk_scores = {
                'high': 3,
                'medium': 2,
                'low': 1
            }
            
            avg_risk_score = np.mean([
                risk_scores[risk_assessment['market_risk']],
                risk_scores[risk_assessment['concentration_risk']],
                risk_scores[risk_assessment['timing_risk']]
            ])
            
            if avg_risk_score >= 2.5:
                risk_assessment['overall_risk'] = 'high'
            elif avg_risk_score <= 1.5:
                risk_assessment['overall_risk'] = 'low'
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"评估风险失败: {e}")
            return {'overall_risk': 'medium'}
    
    def _get_default_analysis(self, strategy_name: str) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            'strategy_name': strategy_name,
            'performance_score': 0.5,
            'risk_score': 0.5,
            'overall_rating': 'C',
            'strengths': ['策略运行正常'],
            'weaknesses': ['需要更多数据进行分析'],
            'suggestions': ['建议进行更长时间的回测'],
            'market_adaptability': {'overall_score': 0.5},
            'risk_assessment': {'overall_risk': 'medium'},
            'analysis_type': 'default',
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def compare_strategies(
        self,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """比较多个策略
        
        Args:
            strategies: 策略列表，每个包含策略名称和回测结果
            
        Returns:
            策略比较结果
        """
        try:
            if len(strategies) < 2:
                return {'error': '至少需要两个策略进行比较'}
            
            comparison_results = []
            
            for strategy in strategies:
                strategy_name = strategy.get('name', '')
                backtest_results = strategy.get('backtest_results', {})
                
                # 分析单个策略
                analysis = await self.analyze_strategy_performance(
                    strategy_name, backtest_results, {}
                )
                
                comparison_results.append({
                    'name': strategy_name,
                    'analysis': analysis
                })
            
            # 排序策略
            comparison_results.sort(
                key=lambda x: x['analysis'].get('performance_score', 0),
                reverse=True
            )
            
            # 生成比较总结
            best_strategy = comparison_results[0]
            worst_strategy = comparison_results[-1]
            
            summary = {
                'total_strategies': len(strategies),
                'best_strategy': best_strategy['name'],
                'worst_strategy': worst_strategy['name'],
                'avg_performance_score': np.mean([
                    result['analysis'].get('performance_score', 0)
                    for result in comparison_results
                ]),
                'comparison_results': comparison_results,
                'recommendations': self._generate_comparison_recommendations(comparison_results)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"策略比较失败: {e}")
            return {'error': f'策略比较失败: {str(e)}'}
    
    def _generate_comparison_recommendations(self, comparison_results: List[Dict[str, Any]]) -> List[str]:
        """生成策略比较建议"""
        recommendations = []
        
        try:
            if len(comparison_results) >= 2:
                best = comparison_results[0]
                worst = comparison_results[-1]
                
                best_score = best['analysis'].get('performance_score', 0)
                worst_score = worst['analysis'].get('performance_score', 0)
                
                if best_score - worst_score > 0.2:
                    recommendations.append(f"建议优先使用{best['name']}策略")
                    recommendations.append(f"{worst['name']}策略需要进一步优化")
                else:
                    recommendations.append("各策略表现相近，可考虑组合使用")
                
                # 分析共同优势和劣势
                all_strengths = []
                all_weaknesses = []
                
                for result in comparison_results:
                    all_strengths.extend(result['analysis'].get('strengths', []))
                    all_weaknesses.extend(result['analysis'].get('weaknesses', []))
                
                # 找出共同问题
                common_weaknesses = []
                for weakness in set(all_weaknesses):
                    if all_weaknesses.count(weakness) >= len(comparison_results) // 2:
                        common_weaknesses.append(weakness)
                
                if common_weaknesses:
                    recommendations.append(f"共同需要改进的方面: {', '.join(common_weaknesses)}")
                    
        except Exception as e:
            self.logger.error(f"生成比较建议失败: {e}")
        
        return recommendations if recommendations else ['建议继续监控各策略表现']


# 全局策略分析器实例
strategy_analyzer = StrategyAnalyzer()