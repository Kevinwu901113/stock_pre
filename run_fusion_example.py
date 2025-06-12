#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融合推荐系统示例脚本
演示如何使用不同的融合策略进行股票推荐
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from recommendation_fusion import RecommendationFusion
from enhanced_fusion_strategy import EnhancedFusionStrategy, FusionMethod

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fusion_recommendation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_enhanced_fusion_strategy(method: str = None, top_n: int = 10, save_results: bool = True) -> List:
    """
    运行增强版融合策略
    
    Args:
        method: 融合方法名称
        top_n: 推荐数量
        save_results: 是否保存结果
        
    Returns:
        推荐结果列表
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"运行增强版融合策略: {method or '默认'}")
    logger.info(f"{'='*50}")
    
    try:
        # 创建增强版融合策略实例
        fusion = EnhancedFusionStrategy('fusion_config.yaml')
        
        # 设置融合方法（如果指定）
        if method:
            try:
                fusion.method = FusionMethod(method)
                logger.info(f"使用融合方法: {fusion.method.value}")
            except ValueError:
                logger.warning(f"无效的融合方法: {method}，使用默认方法: {fusion.method.value}")
        
        # 设置推荐数量
        fusion.top_n = top_n
        
        # 运行融合推荐
        results = fusion.run_fusion()
        
        if results:
            # 打印结果摘要
            fusion.print_results_summary(results)
            
            # 保存结果
            if save_results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_fusion_{fusion.method.value}_{timestamp}.json"
                filepath = fusion.save_results_to_json(results, filename)
                logger.info(f"结果已保存到: {filepath}")
        
        return results
        
    except Exception as e:
        logger.error(f"增强版融合策略运行失败: {e}")
        return []

def run_single_fusion_strategy(strategy: str, stock_codes: List[str] = None) -> Dict:
    """
    运行单个融合策略（原版）
    
    Args:
        strategy: 融合策略名称
        stock_codes: 股票代码列表
        
    Returns:
        推荐结果
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"运行原版融合策略: {strategy}")
    logger.info(f"{'='*50}")
    
    try:
        # 创建融合系统实例
        fusion_system = RecommendationFusion('fusion_config.yaml')
        
        # 设置融合方法
        fusion_system.fusion_method = strategy
        
        # 根据策略调整参数
        if strategy == 'weighted_average':
            fusion_system.ml_weight = 0.4
            fusion_system.factor_weight = 0.6
        elif strategy == 'filter_first':
            fusion_system.ml_threshold = 0.6
            fusion_system.factor_threshold = 0.5
        elif strategy == 'rank_adjustment':
            pass  # 使用默认参数
        
        # 运行推荐
        results = fusion_system.run_fusion_recommendation(
            stock_codes=stock_codes,
            save_to_file=True
        )
        
        # 打印结果摘要
        if 'recommendations' in results and results['recommendations']:
            print(f"\n=== {strategy} 策略结果 ===")
            print(f"推荐时间: {results['metadata']['timestamp']}")
            print(f"推荐数量: {results['metadata']['total_recommendations']}")
            print(f"平均最终得分: {results['summary']['avg_final_score']}")
            print(f"平均ML概率: {results['summary']['avg_ml_probability']:.1%}")
            print(f"平均因子得分: {results['summary']['avg_factor_score']}")
            
            print(f"\nTop 5 推荐:")
            for i, rec in enumerate(results['recommendations'][:5], 1):
                print(f"{i}. {rec['stock_code']} {rec.get('stock_name', '')}")
                print(f"   最终得分: {rec['final_score']:.4f}")
                print(f"   ML概率: {rec['ml_probability']:.1%}")
                print(f"   因子得分: {rec['factor_score']:.2f}")
                print(f"   推荐理由: {rec['recommendation_reason'][:100]}...")
                print()
        else:
            print(f"策略 {strategy} 未产生推荐结果")
            if 'error' in results:
                print(f"错误信息: {results['error']}")
        
        return results
        
    except Exception as e:
        logger.error(f"运行策略 {strategy} 时出错: {e}")
        return {'error': str(e)}

def compare_fusion_strategies(stock_codes: List[str] = None) -> Dict:
    """
    比较不同融合策略的结果
    
    Args:
        stock_codes: 股票代码列表
        
    Returns:
        比较结果
    """
    logger.info("\n开始比较不同融合策略...")
    
    strategies = ['weighted_average', 'filter_first', 'rank_adjustment']
    strategy_results = {}
    
    for strategy in strategies:
        results = run_single_fusion_strategy(strategy, stock_codes)
        strategy_results[strategy] = results
    
    # 生成比较报告
    comparison_report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'strategies_compared': strategies,
        'comparison_summary': {},
        'detailed_results': strategy_results
    }
    
    # 比较各策略的性能指标
    for strategy, results in strategy_results.items():
        if 'recommendations' in results and results['recommendations']:
            comparison_report['comparison_summary'][strategy] = {
                'total_recommendations': len(results['recommendations']),
                'avg_final_score': results['summary']['avg_final_score'],
                'avg_ml_probability': results['summary']['avg_ml_probability'],
                'avg_factor_score': results['summary']['avg_factor_score'],
                'score_range': results['summary']['score_range'],
                'top_stock': results['recommendations'][0]['stock_code'] if results['recommendations'] else None
            }
        else:
            comparison_report['comparison_summary'][strategy] = {
                'error': results.get('error', '无推荐结果')
            }
    
    # 保存比较报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_file = f"results/strategy_comparison_{timestamp}.json"
    
    os.makedirs('results', exist_ok=True)
    
    try:
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        logger.info(f"策略比较报告已保存到: {comparison_file}")
    except Exception as e:
        logger.error(f"保存比较报告失败: {e}")
    
    # 打印比较摘要
    print(f"\n{'='*60}")
    print("策略比较摘要")
    print(f"{'='*60}")
    
    for strategy, summary in comparison_report['comparison_summary'].items():
        print(f"\n{strategy.upper()} 策略:")
        if 'error' in summary:
            print(f"  错误: {summary['error']}")
        else:
            print(f"  推荐数量: {summary['total_recommendations']}")
            print(f"  平均最终得分: {summary['avg_final_score']:.4f}")
            print(f"  平均ML概率: {summary['avg_ml_probability']:.1%}")
            print(f"  平均因子得分: {summary['avg_factor_score']:.2f}")
            print(f"  得分范围: {summary['score_range']['min']:.4f} - {summary['score_range']['max']:.4f}")
            print(f"  Top推荐: {summary['top_stock']}")
    
    return comparison_report

def run_custom_stock_list_example():
    """
    运行自定义股票列表的示例
    """
    logger.info("\n运行自定义股票列表示例...")
    
    # 自定义股票列表（科技股）
    tech_stocks = [
        '000002',  # 万科A
        '002415',  # 海康威视
        '600519',  # 贵州茅台
        '000858',  # 五粮液
        '601318',  # 中国平安
        '600036',  # 招商银行
        '600887',  # 伊利股份
        '000001',  # 平安银行
        '600000',  # 浦发银行
        '000876'   # 新希望
    ]
    
    print(f"\n自定义股票列表: {tech_stocks}")
    
    # 使用加权平均策略
    results = run_single_fusion_strategy('weighted_average', tech_stocks)
    
    return results

def compare_fusion_methods(methods: List[str] = None, top_n: int = 10):
    """
    比较不同融合方法的效果
    
    Args:
        methods: 融合方法列表
        top_n: 推荐数量
    """
    logger.info("\n=== 比较不同融合方法 ===\n")
    
    if methods is None:
        methods = [method.value for method in FusionMethod]
    
    results = {}
    
    for method in methods:
        logger.info(f"\n--- 测试融合方法: {method} ---")
        method_results = run_enhanced_fusion_strategy(method, top_n, save_results=True)
        results[method] = method_results
    
    # 比较结果
    logger.info("\n=== 融合方法比较结果 ===\n")
    print(f"{'融合方法':<20} {'推荐数量':<10} {'平均ML概率':<12} {'平均因子得分':<12} {'高置信度比例':<12}")
    print("-" * 70)
    
    for method, method_results in results.items():
        if not method_results:
            print(f"{method:<20} {'无结果':<10} {'N/A':<12} {'N/A':<12} {'N/A':<12}")
            continue
        
        count = len(method_results)
        avg_ml_prob = sum(r.ml_probability for r in method_results) / count if count > 0 else 0
        avg_factor = sum(r.factor_score for r in method_results) / count if count > 0 else 0
        high_conf = sum(1 for r in method_results if r.confidence_level == 'high')
        high_conf_ratio = high_conf / count if count > 0 else 0
        
        print(f"{method:<20} {count:<10} {avg_ml_prob:<12.3f} {avg_factor:<12.3f} {high_conf_ratio:<12.1%}")
    
    logger.info("\n比较完成！")

def analyze_consensus(results: List):
    """
    分析ML模型和因子模型的一致性
    
    Args:
        results: 推荐结果列表
    """
    if not results:
        logger.info("没有结果可分析")
        return
    
    logger.info("\n=== ML模型与因子模型一致性分析 ===\n")
    
    # 计算一致性
    consensus_count = 0
    divergence_count = 0
    
    for result in results:
        ml_signal = 1 if result.ml_probability > 0.5 else -1
        factor_signal = 1 if result.factor_score > 0 else -1
        
        if ml_signal == factor_signal:
            consensus_count += 1
        else:
            divergence_count += 1
    
    total = consensus_count + divergence_count
    consensus_ratio = consensus_count / total if total > 0 else 0
    
    print(f"一致性比例: {consensus_ratio:.1%} ({consensus_count}/{total})")
    print(f"分歧比例: {1-consensus_ratio:.1%} ({divergence_count}/{total})")
    
    # 按置信度分组
    confidence_groups = {'high': [], 'medium': [], 'low': []}
    for result in results:
        confidence_groups[result.confidence_level].append(result)
    
    print("\n按置信度分组:")
    for level, group in confidence_groups.items():
        if not group:
            continue
        
        group_consensus = sum(1 for r in group if 
                             (r.ml_probability > 0.5 and r.factor_score > 0) or 
                             (r.ml_probability <= 0.5 and r.factor_score <= 0))
        group_ratio = group_consensus / len(group) if group else 0
        
        print(f"  - {level}置信度组({len(group)}只): 一致性比例 {group_ratio:.1%}")

def run_parameter_sensitivity_analysis():
    """
    运行参数敏感性分析
    """
    logger.info("\n运行参数敏感性分析...")
    
    # 测试不同的权重组合
    weight_combinations = [
        (0.2, 0.8),  # 更重视因子
        (0.4, 0.6),  # 默认权重
        (0.6, 0.4),  # 更重视ML
        (0.8, 0.2),  # 主要依赖ML
    ]
    
    sensitivity_results = {}
    
    for ml_weight, factor_weight in weight_combinations:
        logger.info(f"测试权重组合: ML={ml_weight}, Factor={factor_weight}")
        
        try:
            fusion_system = RecommendationFusion('fusion_config.yaml')
            fusion_system.fusion_method = 'weighted_average'
            fusion_system.ml_weight = ml_weight
            fusion_system.factor_weight = factor_weight
            
            results = fusion_system.run_fusion_recommendation(save_to_file=False)
            
            if 'recommendations' in results and results['recommendations']:
                sensitivity_results[f"ml_{ml_weight}_factor_{factor_weight}"] = {
                    'avg_final_score': results['summary']['avg_final_score'],
                    'top_3_stocks': [rec['stock_code'] for rec in results['recommendations'][:3]],
                    'score_range': results['summary']['score_range']
                }
            
        except Exception as e:
            logger.error(f"权重组合 ({ml_weight}, {factor_weight}) 测试失败: {e}")
    
    # 打印敏感性分析结果
    print(f"\n{'='*50}")
    print("参数敏感性分析结果")
    print(f"{'='*50}")
    
    for weight_combo, result in sensitivity_results.items():
        print(f"\n{weight_combo}:")
        print(f"  平均得分: {result['avg_final_score']:.4f}")
        print(f"  Top 3: {', '.join(result['top_3_stocks'])}")
        print(f"  得分范围: {result['score_range']['min']:.4f} - {result['score_range']['max']:.4f}")
    
    return sensitivity_results

def main():
    """
    主函数 - 运行所有示例
    """
    print("\n" + "="*80)
    print("股票推荐系统融合策略演示")
    print("="*80)
    
    try:
        # 1. 比较不同融合策略
        # 1. 运行增强版融合策略示例
        print("\n1. 增强版融合策略示例")
        enhanced_results = run_enhanced_fusion_strategy(method="consensus_boost", top_n=10)
        
        # 分析一致性
        if enhanced_results:
            analyze_consensus(enhanced_results)
        
        # 2. 比较不同融合方法
        print("\n2. 比较不同融合方法")
        compare_fusion_methods(["weighted_average", "filter_first", "consensus_boost"], top_n=5)
        
        # 3. 比较原版融合策略
        print("\n3. 原版融合策略比较")
        comparison_results = compare_fusion_strategies()
        
        # 4. 自定义股票列表示例
        print("\n4. 自定义股票列表示例")
        custom_results = run_custom_stock_list_example()
        
        # 5. 参数敏感性分析
        print("\n5. 参数敏感性分析")
        sensitivity_results = run_parameter_sensitivity_analysis()
        
        print("\n" + "="*80)
        print("所有示例运行完成！")
        print("详细结果已保存到 results/ 目录")
        print("日志文件: fusion_recommendation.log")
        print("="*80)
        print("\n推荐使用增强版融合策略，功能更完善，输出格式更统一！")
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        print(f"\n运行失败: {e}")
        print("请检查配置文件和依赖模块是否正确")

if __name__ == "__main__":
    main()