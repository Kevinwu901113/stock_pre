from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
import json
import asyncio
import importlib
import inspect

from app.models.stock import (
    StrategyResult, Stock, StockPrice, Recommendation,
    StrategyResultResponse, RecommendationType
)
from config.database import cache_manager
from config.settings import settings, STRATEGY_CONFIG
from loguru import logger


class StrategyService:
    """策略服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_manager
        self.strategies = {}
        self._load_strategies()
    
    def _load_strategies(self):
        """加载策略模块"""
        try:
            # 动态加载策略模块
            for category, strategies in STRATEGY_CONFIG.items():
                for strategy_name, config in strategies.items():
                    full_name = f"{category}.{strategy_name}"
                    try:
                        # 动态导入策略模块
                        module_path = f"strategies.{category}.{strategy_name}"
                        module = importlib.import_module(module_path)
                        
                        # 获取策略类
                        strategy_class = getattr(module, config.get('class_name', 'Strategy'))
                        
                        self.strategies[full_name] = {
                            'class': strategy_class,
                            'config': config,
                            'module': module
                        }
                        
                        logger.info(f"策略加载成功: {full_name}")
                        
                    except Exception as e:
                        logger.warning(f"策略加载失败 {full_name}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"策略模块加载失败: {str(e)}")
    
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """获取策略列表"""
        try:
            strategies = []
            
            for strategy_name, strategy_info in self.strategies.items():
                config = strategy_info['config']
                strategy_class = strategy_info['class']
                
                # 获取策略描述
                description = getattr(strategy_class, '__doc__', '') or config.get('description', '')
                
                strategy_data = {
                    'name': strategy_name,
                    'display_name': config.get('display_name', strategy_name),
                    'description': description.strip(),
                    'category': strategy_name.split('.')[0],
                    'enabled': config.get('enabled', True),
                    'parameters': config.get('parameters', {}),
                    'risk_level': config.get('risk_level', 'medium'),
                    'expected_return': config.get('expected_return'),
                    'max_drawdown': config.get('max_drawdown'),
                    'holding_period': config.get('holding_period', '1-5天')
                }
                strategies.append(strategy_data)
            
            return strategies
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {str(e)}")
            raise
    
    async def get_strategy_detail(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略详细信息"""
        try:
            if strategy_name not in self.strategies:
                return None
            
            strategy_info = self.strategies[strategy_name]
            config = strategy_info['config']
            strategy_class = strategy_info['class']
            
            # 获取策略方法信息
            methods = []
            for name, method in inspect.getmembers(strategy_class, predicate=inspect.ismethod):
                if not name.startswith('_'):
                    methods.append({
                        'name': name,
                        'doc': getattr(method, '__doc__', '').strip()
                    })
            
            # 获取最近执行结果
            recent_results = await self._get_recent_strategy_results(strategy_name, 10)
            
            detail = {
                'name': strategy_name,
                'display_name': config.get('display_name', strategy_name),
                'description': getattr(strategy_class, '__doc__', '').strip(),
                'category': strategy_name.split('.')[0],
                'enabled': config.get('enabled', True),
                'parameters': config.get('parameters', {}),
                'risk_level': config.get('risk_level', 'medium'),
                'expected_return': config.get('expected_return'),
                'max_drawdown': config.get('max_drawdown'),
                'holding_period': config.get('holding_period', '1-5天'),
                'methods': methods,
                'recent_results': recent_results,
                'performance_stats': await self._get_strategy_performance_stats(strategy_name)
            }
            
            return detail
            
        except Exception as e:
            logger.error(f"获取策略详情失败: {str(e)}")
            raise
    
    async def get_strategy_config(
        self,
        strategy_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取策略配置"""
        try:
            if strategy_name not in self.strategies:
                return None
            
            return self.strategies[strategy_name]['config']
            
        except Exception as e:
            logger.error(f"获取策略配置失败: {str(e)}")
            raise
    
    async def update_strategy_config(
        self,
        strategy_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新策略配置"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略 {strategy_name} 不存在")
            
            # 更新配置
            self.strategies[strategy_name]['config'].update(config)
            
            # 这里可以将配置保存到数据库或配置文件
            logger.info(f"策略配置更新成功: {strategy_name}")
            
            return {
                'strategy_name': strategy_name,
                'updated_config': config,
                'updated_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"更新策略配置失败: {str(e)}")
            raise
    
    async def execute_strategy(
        self,
        strategy_name: str,
        stock_codes: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行策略"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略 {strategy_name} 不存在")
            
            strategy_info = self.strategies[strategy_name]
            strategy_class = strategy_info['class']
            config = strategy_info['config']
            
            # 合并参数
            final_params = config.get('parameters', {}).copy()
            if parameters:
                final_params.update(parameters)
            
            # 创建策略实例
            strategy_instance = strategy_class(self.db, final_params)
            
            # 获取股票列表
            if not stock_codes:
                stock_codes = await self._get_default_stock_universe()
            
            # 执行策略
            start_time = datetime.now()
            results = await strategy_instance.execute(stock_codes)
            end_time = datetime.now()
            
            # 保存执行结果
            execution_id = await self._save_strategy_results(
                strategy_name,
                results,
                final_params,
                start_time,
                end_time
            )
            
            return {
                'execution_id': execution_id,
                'strategy_name': strategy_name,
                'stock_count': len(stock_codes),
                'results_count': len(results),
                'execution_time': (end_time - start_time).total_seconds(),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"策略执行失败: {str(e)}")
            raise
    
    async def get_strategy_results(
        self,
        strategy_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        size: int = 20
    ) -> List[StrategyResultResponse]:
        """获取策略执行结果"""
        try:
            query = self.db.query(StrategyResult)
            
            # 策略筛选
            if strategy_name:
                query = query.filter(StrategyResult.strategy_name == strategy_name)
            
            # 时间筛选
            if date_from:
                query = query.filter(StrategyResult.created_at >= date_from)
            if date_to:
                query = query.filter(StrategyResult.created_at <= date_to)
            
            # 分页
            offset = (page - 1) * size
            results = query.order_by(
                desc(StrategyResult.created_at)
            ).offset(offset).limit(size).all()
            
            return [StrategyResultResponse.from_orm(result) for result in results]
            
        except Exception as e:
            logger.error(f"获取策略结果失败: {str(e)}")
            raise
    
    async def get_strategy_performance(
        self,
        strategy_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取策略表现统计"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取策略结果
            results = self.db.query(StrategyResult).filter(
                and_(
                    StrategyResult.strategy_name == strategy_name,
                    StrategyResult.created_at >= start_date,
                    StrategyResult.created_at <= end_date
                )
            ).all()
            
            if not results:
                return {
                    'strategy_name': strategy_name,
                    'period_days': days,
                    'total_executions': 0,
                    'total_signals': 0,
                    'success_rate': 0,
                    'average_return': 0,
                    'max_return': 0,
                    'min_return': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0
                }
            
            # 统计数据
            total_executions = len(results)
            total_signals = sum(len(json.loads(r.result_data)) for r in results)
            
            # 计算收益率统计
            returns = []
            for result in results:
                result_data = json.loads(result.result_data)
                for signal in result_data:
                    if 'expected_return' in signal:
                        returns.append(signal['expected_return'])
            
            if returns:
                avg_return = sum(returns) / len(returns)
                max_return = max(returns)
                min_return = min(returns)
                
                # 计算夏普比率(简化)
                if len(returns) > 1:
                    import statistics
                    std_return = statistics.stdev(returns)
                    sharpe_ratio = avg_return / std_return if std_return > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                avg_return = max_return = min_return = sharpe_ratio = 0
            
            # 计算成功率
            success_rate = await self._calculate_strategy_success_rate(strategy_name, days)
            
            return {
                'strategy_name': strategy_name,
                'period_days': days,
                'total_executions': total_executions,
                'total_signals': total_signals,
                'success_rate': round(success_rate, 3),
                'average_return': round(avg_return, 4),
                'max_return': round(max_return, 4),
                'min_return': round(min_return, 4),
                'sharpe_ratio': round(sharpe_ratio, 4),
                'max_drawdown': 0,  # 需要更复杂的计算
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取策略表现失败: {str(e)}")
            raise
    
    async def run_backtest(
        self,
        strategy_name: str,
        start_date: date,
        end_date: date,
        initial_capital: float = 1000000,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """运行策略回测"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略 {strategy_name} 不存在")
            
            strategy_info = self.strategies[strategy_name]
            strategy_class = strategy_info['class']
            config = strategy_info['config']
            
            # 合并参数
            final_params = config.get('parameters', {}).copy()
            if parameters:
                final_params.update(parameters)
            
            # 创建策略实例
            strategy_instance = strategy_class(self.db, final_params)
            
            # 运行回测
            backtest_results = await self._run_backtest_simulation(
                strategy_instance,
                start_date,
                end_date,
                initial_capital
            )
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"回测运行失败: {str(e)}")
            raise
    
    async def create_combined_strategy(
        self,
        name: str,
        strategies: List[Dict[str, Any]],
        combination_method: str = "weighted_average"
    ) -> Dict[str, Any]:
        """创建组合策略"""
        try:
            # 验证策略存在
            for strategy_config in strategies:
                strategy_name = strategy_config['name']
                if strategy_name not in self.strategies:
                    raise ValueError(f"策略 {strategy_name} 不存在")
            
            # 创建组合策略配置
            combined_config = {
                'name': name,
                'type': 'combined',
                'strategies': strategies,
                'combination_method': combination_method,
                'created_at': datetime.now().isoformat()
            }
            
            # 保存组合策略(这里可以保存到数据库)
            logger.info(f"组合策略创建成功: {name}")
            
            return {
                'name': name,
                'config': combined_config,
                'status': 'success',
                'message': '组合策略创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建组合策略失败: {str(e)}")
            raise
    
    async def compare_strategies(
        self,
        strategy_names: List[str],
        days: int = 30
    ) -> Dict[str, Any]:
        """比较多个策略表现"""
        try:
            comparison_results = {}
            
            for strategy_name in strategy_names:
                if strategy_name in self.strategies:
                    performance = await self.get_strategy_performance(strategy_name, days)
                    comparison_results[strategy_name] = performance
            
            # 计算排名
            rankings = self._calculate_strategy_rankings(comparison_results)
            
            return {
                'strategies': comparison_results,
                'rankings': rankings,
                'comparison_date': datetime.now().isoformat(),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"策略比较失败: {str(e)}")
            raise
    
    async def optimize_strategy(
        self,
        strategy_name: str,
        parameter_ranges: Dict[str, Dict[str, Union[int, float]]],
        optimization_target: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """优化策略参数"""
        try:
            if strategy_name not in self.strategies:
                raise ValueError(f"策略 {strategy_name} 不存在")
            
            # 参数优化逻辑(简化实现)
            best_params = {}
            best_score = float('-inf')
            
            # 网格搜索(简化)
            for param_name, param_range in parameter_ranges.items():
                start = param_range.get('start', 0)
                end = param_range.get('end', 100)
                step = param_range.get('step', 10)
                
                current = start
                while current <= end:
                    # 测试参数组合
                    test_params = {param_name: current}
                    
                    # 运行回测评估
                    score = await self._evaluate_parameters(
                        strategy_name,
                        test_params,
                        optimization_target
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_params[param_name] = current
                    
                    current += step
            
            return {
                'strategy_name': strategy_name,
                'optimization_target': optimization_target,
                'best_parameters': best_params,
                'best_score': best_score,
                'optimized_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"策略优化失败: {str(e)}")
            raise
    
    async def _get_default_stock_universe(self) -> List[str]:
        """获取默认股票池"""
        try:
            # 获取活跃股票列表
            stocks = self.db.query(Stock.code).filter(
                and_(
                    Stock.market.in_(['主板', '创业板', '科创板']),
                    Stock.list_date <= datetime.now().date()
                )
            ).limit(1000).all()
            
            return [stock[0] for stock in stocks]
            
        except Exception as e:
            logger.error(f"获取股票池失败: {str(e)}")
            return []
    
    async def _save_strategy_results(
        self,
        strategy_name: str,
        results: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """保存策略执行结果"""
        try:
            # 生成执行ID
            execution_id = f"{strategy_name}_{int(start_time.timestamp())}"
            
            # 保存到数据库
            strategy_result = StrategyResult(
                execution_id=execution_id,
                strategy_name=strategy_name,
                parameters=json.dumps(parameters),
                result_data=json.dumps(results),
                execution_time=(end_time - start_time).total_seconds(),
                created_at=start_time
            )
            
            self.db.add(strategy_result)
            self.db.commit()
            
            logger.info(f"策略结果保存成功: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"保存策略结果失败: {str(e)}")
            self.db.rollback()
            raise
    
    async def _get_recent_strategy_results(
        self,
        strategy_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的策略结果"""
        try:
            results = self.db.query(StrategyResult).filter(
                StrategyResult.strategy_name == strategy_name
            ).order_by(
                desc(StrategyResult.created_at)
            ).limit(limit).all()
            
            return [
                {
                    'execution_id': r.execution_id,
                    'created_at': r.created_at.isoformat(),
                    'execution_time': r.execution_time,
                    'result_count': len(json.loads(r.result_data))
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"获取最近策略结果失败: {str(e)}")
            return []
    
    async def _get_strategy_performance_stats(
        self,
        strategy_name: str
    ) -> Dict[str, Any]:
        """获取策略表现统计"""
        try:
            # 获取30天表现
            performance_30d = await self.get_strategy_performance(strategy_name, 30)
            
            # 获取7天表现
            performance_7d = await self.get_strategy_performance(strategy_name, 7)
            
            return {
                '7_days': performance_7d,
                '30_days': performance_30d
            }
            
        except Exception as e:
            logger.error(f"获取策略表现统计失败: {str(e)}")
            return {}
    
    async def _calculate_strategy_success_rate(
        self,
        strategy_name: str,
        days: int
    ) -> float:
        """计算策略成功率"""
        try:
            # 获取策略推荐
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            recommendations = self.db.query(Recommendation).filter(
                and_(
                    Recommendation.strategy_name == strategy_name,
                    Recommendation.created_at >= start_date,
                    Recommendation.created_at <= end_date
                )
            ).all()
            
            if not recommendations:
                return 0.0
            
            successful_count = 0
            
            for rec in recommendations:
                # 简化的成功率计算
                # 实际应该根据推荐后的价格变化来判断
                if rec.confidence_score > 0.7:
                    successful_count += 1
            
            return successful_count / len(recommendations)
            
        except Exception as e:
            logger.error(f"计算策略成功率失败: {str(e)}")
            return 0.0
    
    async def _run_backtest_simulation(
        self,
        strategy_instance,
        start_date: date,
        end_date: date,
        initial_capital: float
    ) -> Dict[str, Any]:
        """运行回测模拟"""
        try:
            # 简化的回测实现
            # 实际应该包含完整的回测引擎
            
            current_date = start_date
            portfolio_value = initial_capital
            trades = []
            daily_returns = []
            
            while current_date <= end_date:
                # 模拟每日策略执行
                # 这里需要实现完整的回测逻辑
                
                current_date += timedelta(days=1)
            
            # 计算回测指标
            total_return = (portfolio_value - initial_capital) / initial_capital
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'initial_capital': initial_capital,
                'final_value': portfolio_value,
                'total_return': round(total_return, 4),
                'total_trades': len(trades),
                'daily_returns': daily_returns,
                'max_drawdown': 0,  # 需要计算
                'sharpe_ratio': 0,  # 需要计算
                'win_rate': 0  # 需要计算
            }
            
        except Exception as e:
            logger.error(f"回测模拟失败: {str(e)}")
            raise
    
    def _calculate_strategy_rankings(
        self,
        comparison_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """计算策略排名"""
        try:
            rankings = {}
            
            # 按不同指标排名
            metrics = ['success_rate', 'average_return', 'sharpe_ratio']
            
            for metric in metrics:
                sorted_strategies = sorted(
                    comparison_results.items(),
                    key=lambda x: x[1].get(metric, 0),
                    reverse=True
                )
                rankings[metric] = [strategy[0] for strategy in sorted_strategies]
            
            return rankings
            
        except Exception as e:
            logger.error(f"计算策略排名失败: {str(e)}")
            return {}
    
    async def _evaluate_parameters(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        target: str
    ) -> float:
        """评估参数组合"""
        try:
            # 简化的参数评估
            # 实际应该运行回测来评估参数
            
            # 模拟评估分数
            import random
            return random.uniform(0, 1)
            
        except Exception as e:
            logger.error(f"参数评估失败: {str(e)}")
            return 0.0