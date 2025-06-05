"""策略分析器

使用AI模型对量化策略进行分析、优化和评估。
包含机器学习模型训练和预测功能。"""

import os
import sys
import joblib
import pickle
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost未安装，将使用其他算法")

from .model_manager import model_manager
from config.settings import settings
from config.database import get_db
from backend.app.models.stock import StockPrice, Stock


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
        
        # 机器学习模型相关
        self.models = {}
        self.scalers = {}
        self.model_dir = "ai/models"
        os.makedirs(self.model_dir, exist_ok=True)
    
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


    def prepare_ml_features(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """准备机器学习特征
        
        Args:
            stock_data: 股票价格数据
            
        Returns:
            特征数据框
        """
        try:
            df = stock_data.copy()
            df = df.sort_values('trade_date')
            
            # 基础价格特征
            df['price_change'] = df['close_price'].pct_change()
            df['high_low_ratio'] = df['high_price'] / df['low_price']
            df['open_close_ratio'] = df['open_price'] / df['close_price']
            
            # 移动平均线特征
            for period in [5, 10, 20, 30]:
                df[f'ma_{period}'] = df['close_price'].rolling(window=period).mean()
                df[f'price_ma_{period}_ratio'] = df['close_price'] / df[f'ma_{period}']
                df[f'ma_{period}_slope'] = df[f'ma_{period}'].pct_change()
            
            # 技术指标特征
            df['rsi'] = self.calculate_rsi(df['close_price'])
            df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
            df['turnover_ma_ratio'] = df['turnover_rate'] / df['turnover_rate'].rolling(window=20).mean()
            
            # MACD特征
            macd_data = self.calculate_macd_features(df['close_price'])
            df = pd.concat([df, macd_data], axis=1)
            
            # 布林带特征
            bb_data = self.calculate_bollinger_features(df['close_price'])
            df = pd.concat([df, bb_data], axis=1)
            
            # 波动率特征
            df['volatility_5'] = df['price_change'].rolling(window=5).std()
            df['volatility_20'] = df['price_change'].rolling(window=20).std()
            
            # 成交量特征
            df['volume_change'] = df['volume'].pct_change()
            df['volume_price_trend'] = df['volume_change'] * df['price_change']
            
            # 市场强度特征
            df['market_strength'] = (df['close_price'] - df['low_price']) / (df['high_price'] - df['low_price'])
            
            # 连续涨跌天数
            df['consecutive_up'] = (df['price_change'] > 0).astype(int).groupby(
                (df['price_change'] <= 0).cumsum()).cumsum()
            df['consecutive_down'] = (df['price_change'] < 0).astype(int).groupby(
                (df['price_change'] >= 0).cumsum()).cumsum()
            
            return df
            
        except Exception as e:
            self.logger.error(f"准备特征失败: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd_features(self, prices: pd.Series) -> pd.DataFrame:
        """计算MACD特征"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd_line': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram,
            'macd_above_signal': (macd_line > signal_line).astype(int)
        })
    
    def calculate_bollinger_features(self, prices: pd.Series, period: int = 20) -> pd.DataFrame:
        """计算布林带特征"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = ma + (2 * std)
        lower_band = ma - (2 * std)
        
        return pd.DataFrame({
            'bb_upper': upper_band,
            'bb_middle': ma,
            'bb_lower': lower_band,
            'bb_width': (upper_band - lower_band) / ma,
            'bb_position': (prices - lower_band) / (upper_band - lower_band)
        })
    
    def create_labels(self, df: pd.DataFrame, target_return: float = 0.02) -> pd.Series:
        """创建训练标签
        
        Args:
            df: 数据框
            target_return: 目标收益率阈值
            
        Returns:
            标签序列 (1: 买入, 0: 不买入)
        """
        # 计算次日收益率
        df['next_day_return'] = df['close_price'].shift(-1) / df['close_price'] - 1
        
        # 创建二分类标签
        labels = (df['next_day_return'] > target_return).astype(int)
        
        return labels
    
    def get_training_data(self, start_date: date, end_date: date, min_samples: int = 1000) -> Tuple[pd.DataFrame, pd.Series]:
        """获取训练数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            min_samples: 最小样本数
            
        Returns:
            特征数据和标签
        """
        try:
            db = next(get_db())
            
            # 获取活跃股票
            active_stocks = db.query(Stock).filter(
                Stock.is_active == True,
                ~Stock.name.like('%ST%'),
                ~Stock.name.like('%退%')
            ).limit(500).all()  # 限制股票数量避免内存问题
            
            all_features = []
            all_labels = []
            
            for stock in active_stocks:
                try:
                    # 获取股票价格数据
                    prices = db.query(StockPrice).filter(
                        StockPrice.stock_code == stock.code,
                        StockPrice.trade_date >= start_date,
                        StockPrice.trade_date <= end_date
                    ).order_by(StockPrice.trade_date).all()
                    
                    if len(prices) < 60:  # 至少需要60天数据
                        continue
                    
                    # 转换为DataFrame
                    df = pd.DataFrame([{
                        'trade_date': p.trade_date,
                        'open_price': p.open_price,
                        'high_price': p.high_price,
                        'low_price': p.low_price,
                        'close_price': p.close_price,
                        'volume': p.volume,
                        'turnover_rate': p.turnover_rate or 0
                    } for p in prices])
                    
                    # 准备特征
                    features_df = self.prepare_ml_features(df)
                    
                    # 创建标签
                    labels = self.create_labels(features_df)
                    
                    # 选择特征列
                    feature_columns = [
                        'price_change', 'high_low_ratio', 'open_close_ratio',
                        'price_ma_5_ratio', 'price_ma_10_ratio', 'price_ma_20_ratio',
                        'ma_5_slope', 'ma_10_slope', 'ma_20_slope',
                        'rsi', 'volume_ma_ratio', 'turnover_ma_ratio',
                        'macd_line', 'macd_histogram', 'macd_above_signal',
                        'bb_width', 'bb_position',
                        'volatility_5', 'volatility_20',
                        'volume_change', 'volume_price_trend',
                        'market_strength', 'consecutive_up', 'consecutive_down'
                    ]
                    
                    # 过滤有效数据
                    valid_data = features_df[feature_columns + ['trade_date']].dropna()
                    valid_labels = labels[valid_data.index]
                    
                    if len(valid_data) > 30:
                        all_features.append(valid_data[feature_columns])
                        all_labels.append(valid_labels)
                        
                except Exception as e:
                    self.logger.error(f"处理股票{stock.code}数据失败: {e}")
                    continue
            
            if not all_features:
                raise ValueError("没有获取到有效的训练数据")
            
            # 合并所有数据
            X = pd.concat(all_features, ignore_index=True)
            y = pd.concat(all_labels, ignore_index=True)
            
            # 检查样本数量
            if len(X) < min_samples:
                self.logger.warning(f"训练样本数量({len(X)})少于最小要求({min_samples})")
            
            self.logger.info(f"获取训练数据完成: {len(X)}个样本, {len(X.columns)}个特征")
            self.logger.info(f"正样本比例: {y.mean():.2%}")
            
            return X, y
            
        except Exception as e:
            self.logger.error(f"获取训练数据失败: {e}")
            return pd.DataFrame(), pd.Series()
        finally:
            db.close()
    
    def train_model(self, model_name: str = 'logistic_regression', test_size: float = 0.2) -> Dict[str, Any]:
        """训练模型
        
        Args:
            model_name: 模型名称 ('logistic_regression', 'random_forest', 'xgboost')
            test_size: 测试集比例
            
        Returns:
            训练结果
        """
        try:
            self.logger.info(f"开始训练{model_name}模型")
            
            # 获取训练数据
            end_date = date.today() - timedelta(days=1)
            start_date = end_date - timedelta(days=365 * 2)  # 2年数据
            
            X, y = self.get_training_data(start_date, end_date)
            
            if X.empty or y.empty:
                raise ValueError("没有可用的训练数据")
            
            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # 创建模型管道
            if model_name == 'logistic_regression':
                model = Pipeline([
                    ('scaler', StandardScaler()),
                    ('classifier', LogisticRegression(random_state=42, max_iter=1000))
                ])
            elif model_name == 'random_forest':
                model = Pipeline([
                    ('scaler', StandardScaler()),
                    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
                ])
            elif model_name == 'xgboost' and XGBOOST_AVAILABLE:
                model = Pipeline([
                    ('scaler', StandardScaler()),
                    ('classifier', xgb.XGBClassifier(random_state=42))
                ])
            else:
                raise ValueError(f"不支持的模型类型: {model_name}")
            
            # 训练模型
            model.fit(X_train, y_train)
            
            # 预测
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # 评估模型
            auc_score = roc_auc_score(y_test, y_pred_proba)
            
            # 交叉验证
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
            
            # 保存模型
            model_file = os.path.join(self.model_dir, f"{model_name}_model.joblib")
            joblib.dump(model, model_file)
            
            # 保存特征名称
            feature_names_file = os.path.join(self.model_dir, f"{model_name}_features.pkl")
            with open(feature_names_file, 'wb') as f:
                pickle.dump(list(X.columns), f)
            
            self.models[model_name] = model
            
            results = {
                'model_name': model_name,
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'auc_score': auc_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                'model_file': model_file,
                'feature_names_file': feature_names_file
            }
            
            self.logger.info(f"模型训练完成: AUC={auc_score:.3f}, CV={cv_scores.mean():.3f}±{cv_scores.std():.3f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"训练模型失败: {e}")
            return {}
    
    def load_model(self, model_name: str) -> bool:
        """加载已训练的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否加载成功
        """
        try:
            model_file = os.path.join(self.model_dir, f"{model_name}_model.joblib")
            
            if not os.path.exists(model_file):
                self.logger.warning(f"模型文件不存在: {model_file}")
                return False
            
            model = joblib.load(model_file)
            self.models[model_name] = model
            
            self.logger.info(f"模型{model_name}加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型{model_name}失败: {e}")
            return False
    
    def predict_stock(self, model_name: str, stock_code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """使用模型预测股票
        
        Args:
            model_name: 模型名称
            stock_code: 股票代码
            days: 历史数据天数
            
        Returns:
            预测结果
        """
        try:
            if model_name not in self.models:
                if not self.load_model(model_name):
                    return None
            
            model = self.models[model_name]
            
            # 获取股票数据
            db = next(get_db())
            end_date = date.today()
            start_date = end_date - timedelta(days=days + 30)  # 多获取一些数据用于计算指标
            
            prices = db.query(StockPrice).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trade_date >= start_date,
                StockPrice.trade_date <= end_date
            ).order_by(StockPrice.trade_date).all()
            
            if len(prices) < 30:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame([{
                'trade_date': p.trade_date,
                'open_price': p.open_price,
                'high_price': p.high_price,
                'low_price': p.low_price,
                'close_price': p.close_price,
                'volume': p.volume,
                'turnover_rate': p.turnover_rate or 0
            } for p in prices])
            
            # 准备特征
            features_df = self.prepare_ml_features(df)
            
            # 获取最新数据
            latest_data = features_df.iloc[-1:]
            
            # 选择特征列（需要与训练时一致）
            feature_columns = [
                'price_change', 'high_low_ratio', 'open_close_ratio',
                'price_ma_5_ratio', 'price_ma_10_ratio', 'price_ma_20_ratio',
                'ma_5_slope', 'ma_10_slope', 'ma_20_slope',
                'rsi', 'volume_ma_ratio', 'turnover_ma_ratio',
                'macd_line', 'macd_histogram', 'macd_above_signal',
                'bb_width', 'bb_position',
                'volatility_5', 'volatility_20',
                'volume_change', 'volume_price_trend',
                'market_strength', 'consecutive_up', 'consecutive_down'
            ]
            
            X = latest_data[feature_columns]
            
            if X.isnull().any().any():
                self.logger.warning(f"股票{stock_code}特征数据包含缺失值")
                return None
            
            # 预测
            prediction = model.predict(X)[0]
            prediction_proba = model.predict_proba(X)[0]
            
            result = {
                'stock_code': stock_code,
                'prediction': int(prediction),
                'buy_probability': float(prediction_proba[1]),
                'confidence': float(max(prediction_proba)),
                'model_name': model_name,
                'prediction_date': datetime.now(),
                'features': X.iloc[0].to_dict()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"预测失败 {stock_code}: {e}")
            return None
         finally:
             db.close()


# 全局策略分析器实例
strategy_analyzer = StrategyAnalyzer()