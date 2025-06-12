#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票推荐系统使用示例
演示如何使用不同的配置策略运行系统
"""

import os
import sys
from main import StockRecommendationSystem

def run_conservative_strategy():
    """运行保守策略示例"""
    print("=== 保守策略示例 ===")
    system = StockRecommendationSystem(
        stock_universe='conservative',
        factor_strategy='conservative',
        time_period='long_term'
    )
    
    recommendations = system.run_recommendation(top_n=5)
    print(f"保守策略推荐了 {len(recommendations)} 只股票\n")
    return recommendations

def run_aggressive_strategy():
    """运行激进策略示例"""
    print("=== 激进策略示例 ===")
    system = StockRecommendationSystem(
        stock_universe='aggressive',
        factor_strategy='momentum_focused',
        time_period='short_term'
    )
    
    recommendations = system.run_recommendation(top_n=10)
    print(f"激进策略推荐了 {len(recommendations)} 只股票\n")
    return recommendations

def run_capital_flow_strategy():
    """运行资金流向策略示例"""
    print("=== 资金流向策略示例 ===")
    system = StockRecommendationSystem(
        stock_universe='default',
        factor_strategy='capital_flow_focused',
        time_period='medium_term'
    )
    
    recommendations = system.run_recommendation(top_n=8)
    print(f"资金流向策略推荐了 {len(recommendations)} 只股票\n")
    return recommendations

def compare_strategies():
    """比较不同策略的结果"""
    print("=== 策略比较 ===")
    
    strategies = [
        ('保守策略', 'conservative', 'conservative', 'long_term'),
        ('激进策略', 'aggressive', 'momentum_focused', 'short_term'),
        ('资金流向策略', 'default', 'capital_flow_focused', 'medium_term'),
        ('默认策略', 'default', 'default', 'default')
    ]
    
    results = {}
    
    for name, universe, factor, period in strategies:
        try:
            system = StockRecommendationSystem(
                stock_universe=universe,
                factor_strategy=factor,
                time_period=period
            )
            
            recommendations = system.run_recommendation(top_n=5)
            results[name] = recommendations
            print(f"{name}: {len(recommendations)} 只推荐股票")
            
        except Exception as e:
            print(f"{name} 运行失败: {e}")
            results[name] = []
    
    return results

def main():
    """主函数"""
    print("股票推荐系统策略示例\n")
    
    try:
        # 运行不同策略示例
        conservative_results = run_conservative_strategy()
        aggressive_results = run_aggressive_strategy()
        capital_flow_results = run_capital_flow_strategy()
        
        # 比较策略
        comparison_results = compare_strategies()
        
        print("\n=== 总结 ===")
        print("所有策略示例运行完成！")
        print("您可以根据市场情况和个人风险偏好选择合适的策略。")
        
    except Exception as e:
        print(f"示例运行出错: {e}")

if __name__ == "__main__":
    main()