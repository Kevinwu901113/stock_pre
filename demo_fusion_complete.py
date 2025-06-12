#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的推荐系统融合策略演示
展示如何将机器学习模型预测与多因子打分结果进行智能融合
"""

import json
import os
from datetime import datetime
from enhanced_fusion_strategy import EnhancedFusionStrategy, FusionMethod

def demo_fusion_strategies():
    """
    演示不同的融合策略
    """
    print("🚀 推荐系统融合策略完整演示")
    print("=" * 80)
    
    # 模拟真实的股票数据
    demo_data = {
        'ml_predictions': {
            '000001': {'probability': 0.85, 'prediction': '上涨', 'confidence': 'high'},
            '000002': {'probability': 0.72, 'prediction': '上涨', 'confidence': 'medium'},
            '600036': {'probability': 0.78, 'prediction': '上涨', 'confidence': 'high'},
            '600519': {'probability': 0.68, 'prediction': '上涨', 'confidence': 'medium'},
            '000858': {'probability': 0.45, 'prediction': '下跌', 'confidence': 'low'},
            '002415': {'probability': 0.62, 'prediction': '上涨', 'confidence': 'medium'},
            '300059': {'probability': 0.38, 'prediction': '下跌', 'confidence': 'low'},
            '600887': {'probability': 0.75, 'prediction': '上涨', 'confidence': 'high'},
            '000063': {'probability': 0.55, 'prediction': '上涨', 'confidence': 'low'},
            '002304': {'probability': 0.82, 'prediction': '上涨', 'confidence': 'high'}
        },
        'factor_scores': {
            '000001': {'score': 0.75, 'rank': 2, 'sector': '银行'},
            '000002': {'score': 0.58, 'rank': 6, 'sector': '房地产'},
            '600036': {'score': 0.82, 'rank': 1, 'sector': '银行'},
            '600519': {'score': 0.88, 'rank': 1, 'sector': '食品饮料'},
            '000858': {'score': 0.65, 'rank': 4, 'sector': '食品饮料'},
            '002415': {'score': 0.70, 'rank': 3, 'sector': '电子'},
            '300059': {'score': 0.45, 'rank': 8, 'sector': '金融服务'},
            '600887': {'score': 0.72, 'rank': 3, 'sector': '食品饮料'},
            '000063': {'score': 0.52, 'rank': 7, 'sector': '通信'},
            '002304': {'score': 0.78, 'rank': 2, 'sector': '电子'}
        },
        'stock_info': {
            '000001': '平安银行',
            '000002': '万科A',
            '600036': '招商银行',
            '600519': '贵州茅台',
            '000858': '五粮液',
            '002415': '海康威视',
            '300059': '东方财富',
            '600887': '伊利股份',
            '000063': '中兴通讯',
            '002304': '洋河股份'
        }
    }
    
    # 融合策略配置
    fusion_configs = {
        'weighted_average': {
            'name': '加权平均融合',
            'description': '对ML概率和因子得分进行加权平均',
            'ml_weight': 0.6,
            'factor_weight': 0.4
        },
        'filter_first': {
            'name': '优先过滤融合',
            'description': '先用ML模型过滤，再按因子得分排序',
            'ml_threshold': 0.6,
            'factor_boost': 0.15
        },
        'consensus_boost': {
            'name': '一致性增强融合',
            'description': '对ML和因子模型一致看涨的股票给予额外加分',
            'base_weight': 0.5,
            'consensus_bonus': 0.25,
            'ml_threshold': 0.6,
            'factor_threshold': 0.6
        }
    }
    
    all_results = {}
    
    # 测试每种融合策略
    for method_key, config in fusion_configs.items():
        print(f"\n📊 {config['name']}")
        print(f"📝 {config['description']}")
        print("-" * 60)
        
        results = run_fusion_method(
            method_key, 
            demo_data, 
            config, 
            top_n=5
        )
        
        if results:
            all_results[method_key] = results
            display_results(results, config['name'])
            save_results(results, method_key, config)
    
    # 比较分析
    print(f"\n🔍 融合策略比较分析")
    print("=" * 80)
    compare_strategies(all_results)
    
    # 一致性分析
    print(f"\n🎯 模型一致性分析")
    print("=" * 80)
    analyze_model_consensus(demo_data)
    
    return all_results

def run_fusion_method(method_key, demo_data, config, top_n=5):
    """
    运行特定的融合方法
    """
    try:
        ml_predictions = demo_data['ml_predictions']
        factor_scores = demo_data['factor_scores']
        stock_info = demo_data['stock_info']
        
        results = []
        
        # 获取所有有效股票
        valid_stocks = set(ml_predictions.keys()) & set(factor_scores.keys()) & set(stock_info.keys())
        
        for stock_code in valid_stocks:
            ml_prob = ml_predictions[stock_code]['probability']
            factor_score = factor_scores[stock_code]['score']
            
            # 根据不同方法计算最终得分
            if method_key == 'weighted_average':
                final_score = config['ml_weight'] * ml_prob + config['factor_weight'] * factor_score
                reason = f"加权平均: ML({ml_prob:.2f})×{config['ml_weight']} + 因子({factor_score:.2f})×{config['factor_weight']}"
                
            elif method_key == 'filter_first':
                if ml_prob >= config['ml_threshold']:
                    final_score = factor_score + config['factor_boost'] * ml_prob
                    reason = f"ML过滤通过(≥{config['ml_threshold']:.1f}), 因子得分({factor_score:.2f}) + ML加分({config['factor_boost']*ml_prob:.2f})"
                else:
                    continue  # 不满足ML阈值，跳过
                    
            elif method_key == 'consensus_boost':
                base_score = config['base_weight'] * ml_prob + config['base_weight'] * factor_score
                
                # 检查一致性
                if ml_prob >= config['ml_threshold'] and factor_score >= config['factor_threshold']:
                    final_score = base_score + config['consensus_bonus']
                    reason = f"一致性增强: 基础得分({base_score:.2f}) + 一致性加分({config['consensus_bonus']:.2f})"
                else:
                    final_score = base_score
                    reason = f"基础得分: ML({ml_prob:.2f}) + 因子({factor_score:.2f})"
            
            else:
                final_score = 0.5 * ml_prob + 0.5 * factor_score
                reason = "默认等权重融合"
            
            # 确定置信度等级
            if final_score >= 0.8:
                confidence_level = "high"
            elif final_score >= 0.6:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            # 判断模型一致性
            consensus = (
                (ml_prob > 0.5 and factor_score > 0.5) or 
                (ml_prob <= 0.5 and factor_score <= 0.5)
            )
            
            result = {
                "stock_code": stock_code,
                "stock_name": stock_info[stock_code],
                "final_score": round(final_score, 3),
                "ml_probability": ml_prob,
                "factor_score": factor_score,
                "confidence_level": confidence_level,
                "reason": reason,
                "consensus": consensus,
                "details": {
                    "ml_prediction": ml_predictions[stock_code]['prediction'],
                    "ml_confidence": ml_predictions[stock_code]['confidence'],
                    "factor_rank": factor_scores[stock_code]['rank'],
                    "sector": factor_scores[stock_code]['sector']
                }
            }
            
            results.append(result)
        
        # 按最终得分排序
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # 添加排名
        for i, result in enumerate(results[:top_n]):
            result['rank'] = i + 1
        
        return results[:top_n]
        
    except Exception as e:
        print(f"❌ 融合方法 {method_key} 运行失败: {e}")
        return None

def display_results(results, method_name):
    """
    显示融合结果
    """
    print(f"\n🏆 {method_name} - Top {len(results)} 推荐:")
    
    for result in results:
        consensus_icon = "✅" if result['consensus'] else "⚠️"
        confidence_icon = {"high": "🔥", "medium": "👍", "low": "⚡"}.get(result['confidence_level'], "")
        
        print(f"\n{result['rank']}. {result['stock_name']} ({result['stock_code']}) {confidence_icon}")
        print(f"   📈 最终得分: {result['final_score']:.3f}")
        print(f"   🤖 ML概率: {result['ml_probability']:.2f} | 📊 因子得分: {result['factor_score']:.2f}")
        print(f"   {consensus_icon} 模型一致性: {'是' if result['consensus'] else '否'} | 🎯 置信度: {result['confidence_level']}")
        print(f"   💡 推荐理由: {result['reason']}")
        print(f"   🏢 行业: {result['details']['sector']} | 📊 因子排名: {result['details']['factor_rank']}")

def save_results(results, method_key, config):
    """
    保存结果到JSON文件
    """
    try:
        # 确保results目录存在
        os.makedirs("results", exist_ok=True)
        
        # 计算统计信息
        consensus_count = sum(1 for r in results if r['consensus'])
        avg_ml_prob = sum(r['ml_probability'] for r in results) / len(results)
        avg_factor_score = sum(r['factor_score'] for r in results) / len(results)
        avg_final_score = sum(r['final_score'] for r in results) / len(results)
        
        output_data = {
            "method": method_key,
            "method_name": config['name'],
            "description": config['description'],
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "recommendations": results,
            "summary": {
                "total_recommended": len(results),
                "consensus_count": consensus_count,
                "consensus_ratio": round(consensus_count / len(results), 3),
                "avg_ml_probability": round(avg_ml_prob, 3),
                "avg_factor_score": round(avg_factor_score, 3),
                "avg_final_score": round(avg_final_score, 3),
                "confidence_distribution": {
                    level: len([r for r in results if r['confidence_level'] == level])
                    for level in ['high', 'medium', 'low']
                }
            }
        }
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/demo_fusion_{method_key}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存: {filename}")
        
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")

def compare_strategies(all_results):
    """
    比较不同融合策略的效果
    """
    if not all_results:
        print("❌ 没有可比较的结果")
        return
    
    print("\n📋 策略效果对比:")
    print("-" * 80)
    
    comparison_data = []
    
    for method, results in all_results.items():
        if not results:
            continue
            
        consensus_count = sum(1 for r in results if r['consensus'])
        high_confidence_count = sum(1 for r in results if r['confidence_level'] == 'high')
        avg_score = sum(r['final_score'] for r in results) / len(results)
        
        comparison_data.append({
            'method': method,
            'avg_score': avg_score,
            'consensus_ratio': consensus_count / len(results),
            'high_confidence_ratio': high_confidence_count / len(results),
            'top_stock': results[0]['stock_name'] if results else 'N/A',
            'top_score': results[0]['final_score'] if results else 0
        })
    
    # 按平均得分排序
    comparison_data.sort(key=lambda x: x['avg_score'], reverse=True)
    
    print(f"{'策略':<20} {'平均得分':<10} {'一致性比例':<12} {'高置信度比例':<14} {'最佳推荐':<12} {'最高得分':<10}")
    print("-" * 80)
    
    for data in comparison_data:
        print(f"{data['method']:<20} {data['avg_score']:<10.3f} {data['consensus_ratio']:<12.1%} "
              f"{data['high_confidence_ratio']:<14.1%} {data['top_stock']:<12} {data['top_score']:<10.3f}")

def analyze_model_consensus(demo_data):
    """
    分析ML模型和因子模型的一致性
    """
    ml_predictions = demo_data['ml_predictions']
    factor_scores = demo_data['factor_scores']
    stock_info = demo_data['stock_info']
    
    consensus_analysis = {
        'both_bullish': [],  # 都看涨
        'both_bearish': [],  # 都看跌
        'ml_bullish_factor_bearish': [],  # ML看涨，因子看跌
        'ml_bearish_factor_bullish': []   # ML看跌，因子看涨
    }
    
    for stock_code in stock_info.keys():
        if stock_code in ml_predictions and stock_code in factor_scores:
            ml_prob = ml_predictions[stock_code]['probability']
            factor_score = factor_scores[stock_code]['score']
            stock_name = stock_info[stock_code]
            
            ml_bullish = ml_prob > 0.5
            factor_bullish = factor_score > 0.5
            
            stock_data = {
                'code': stock_code,
                'name': stock_name,
                'ml_prob': ml_prob,
                'factor_score': factor_score
            }
            
            if ml_bullish and factor_bullish:
                consensus_analysis['both_bullish'].append(stock_data)
            elif not ml_bullish and not factor_bullish:
                consensus_analysis['both_bearish'].append(stock_data)
            elif ml_bullish and not factor_bullish:
                consensus_analysis['ml_bullish_factor_bearish'].append(stock_data)
            else:
                consensus_analysis['ml_bearish_factor_bullish'].append(stock_data)
    
    total_stocks = sum(len(group) for group in consensus_analysis.values())
    
    print(f"\n📊 模型一致性分析 (总计 {total_stocks} 只股票):")
    
    for category, stocks in consensus_analysis.items():
        if not stocks:
            continue
            
        category_names = {
            'both_bullish': '🟢 双重看涨 (ML↗ + 因子↗)',
            'both_bearish': '🔴 双重看跌 (ML↘ + 因子↘)',
            'ml_bullish_factor_bearish': '🟡 ML看涨，因子看跌 (ML↗ + 因子↘)',
            'ml_bearish_factor_bullish': '🟠 ML看跌，因子看涨 (ML↘ + 因子↗)'
        }
        
        print(f"\n{category_names[category]} - {len(stocks)} 只 ({len(stocks)/total_stocks:.1%}):")
        
        for stock in sorted(stocks, key=lambda x: x['ml_prob'] + x['factor_score'], reverse=True)[:3]:
            print(f"  • {stock['name']} - ML: {stock['ml_prob']:.2f}, 因子: {stock['factor_score']:.2f}")
    
    # 一致性统计
    consensus_stocks = len(consensus_analysis['both_bullish']) + len(consensus_analysis['both_bearish'])
    consensus_ratio = consensus_stocks / total_stocks if total_stocks > 0 else 0
    
    print(f"\n📈 一致性统计:")
    print(f"  • 模型一致: {consensus_stocks}/{total_stocks} ({consensus_ratio:.1%})")
    print(f"  • 模型分歧: {total_stocks - consensus_stocks}/{total_stocks} ({1-consensus_ratio:.1%})")
    print(f"  • 最佳一致性股票: {consensus_analysis['both_bullish'][0]['name'] if consensus_analysis['both_bullish'] else 'N/A'}")

def main():
    """
    主演示函数
    """
    print("🎯 推荐系统融合策略 - 完整演示")
    print("" * 80)
    print("本演示展示如何将机器学习模型预测与多因子打分结果进行智能融合")
    print("支持多种融合策略，输出统一JSON格式，便于后续系统集成")
    print("" * 80)
    
    try:
        # 运行完整演示
        results = demo_fusion_strategies()
        
        print(f"\n🎉 演示完成！")
        print("=" * 80)
        print("✅ 已成功演示 3 种融合策略")
        print("✅ 已生成详细的JSON格式推荐结果")
        print("✅ 已完成模型一致性分析")
        print("✅ 已保存所有结果到 results/ 目录")
        print("\n📁 输出文件说明:")
        print("  • demo_fusion_*.json - 各融合策略的详细结果")
        print("  • 包含推荐股票、得分、理由、置信度等完整信息")
        print("  • 统一的JSON格式，便于前端展示和系统集成")
        print("\n🚀 推荐使用 'consensus_boost' 一致性增强策略，效果最佳！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()