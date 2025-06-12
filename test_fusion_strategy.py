#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版融合策略的核心功能
"""

import json
import os
from datetime import datetime
from enhanced_fusion_strategy import EnhancedFusionStrategy, FusionMethod

def create_mock_data():
    """
    创建模拟数据用于测试
    """
    # 模拟ML预测结果
    ml_predictions = {
        '000001': {'probability': 0.75, 'prediction': '上涨'},
        '000002': {'probability': 0.65, 'prediction': '上涨'},
        '000858': {'probability': 0.45, 'prediction': '下跌'},
        '600036': {'probability': 0.80, 'prediction': '上涨'},
        '600519': {'probability': 0.70, 'prediction': '上涨'},
        '000858': {'probability': 0.55, 'prediction': '上涨'},
        '002415': {'probability': 0.60, 'prediction': '上涨'},
        '300059': {'probability': 0.40, 'prediction': '下跌'},
        '600887': {'probability': 0.85, 'prediction': '上涨'},
        '000063': {'probability': 0.50, 'prediction': '上涨'}
    }
    
    # 模拟因子得分结果
    factor_scores = {
        '000001': {'score': 0.68, 'rank': 3},
        '000002': {'score': 0.45, 'rank': 7},
        '000858': {'score': 0.72, 'rank': 2},
        '600036': {'score': 0.55, 'rank': 5},
        '600519': {'score': 0.80, 'rank': 1},
        '000858': {'score': 0.40, 'rank': 8},
        '002415': {'score': 0.60, 'rank': 4},
        '300059': {'score': 0.75, 'rank': 2},
        '600887': {'score': 0.50, 'rank': 6},
        '000063': {'score': 0.35, 'rank': 9}
    }
    
    # 模拟股票基本信息
    stock_info = {
        '000001': '平安银行',
        '000002': '万科A',
        '000858': '五粮液',
        '600036': '招商银行',
        '600519': '贵州茅台',
        '002415': '海康威视',
        '300059': '东方财富',
        '600887': '伊利股份',
        '000063': '中兴通讯'
    }
    
    return ml_predictions, factor_scores, stock_info

def test_fusion_method(method_name, top_n=5):
    """
    测试特定的融合方法
    """
    print(f"\n{'='*60}")
    print(f"测试融合方法: {method_name}")
    print(f"{'='*60}")
    
    try:
        # 创建模拟数据
        ml_predictions, factor_scores, stock_info = create_mock_data()
        
        # 初始化融合策略
        fusion = EnhancedFusionStrategy()
        
        # 模拟融合过程
        results = []
        
        # 获取所有股票代码
        all_stocks = set(ml_predictions.keys()) & set(factor_scores.keys())
        
        for stock_code in all_stocks:
            if stock_code in stock_info:
                ml_prob = ml_predictions[stock_code]['probability']
                factor_score = factor_scores[stock_code]['score']
                
                # 根据不同方法计算最终得分
                if method_name == "weighted_average":
                    final_score = 0.6 * ml_prob + 0.4 * factor_score
                    reason = f"加权平均: ML({ml_prob:.2f}) * 0.6 + 因子({factor_score:.2f}) * 0.4"
                    
                elif method_name == "filter_first":
                    if ml_prob > 0.5:
                        final_score = factor_score + 0.1 * ml_prob
                        reason = f"ML过滤通过，因子得分({factor_score:.2f}) + ML加分({0.1*ml_prob:.2f})"
                    else:
                        continue
                        
                elif method_name == "consensus_boost":
                    base_score = 0.5 * ml_prob + 0.5 * factor_score
                    if ml_prob > 0.6 and factor_score > 0.5:
                        final_score = base_score + 0.2  # 一致性加分
                        reason = f"一致性增强: 基础得分({base_score:.2f}) + 一致性加分(0.2)"
                    else:
                        final_score = base_score
                        reason = f"基础得分: ML({ml_prob:.2f}) + 因子({factor_score:.2f})"
                        
                else:
                    final_score = 0.5 * ml_prob + 0.5 * factor_score
                    reason = "默认等权重融合"
                
                # 确定置信度
                if final_score > 0.7:
                    confidence = "high"
                elif final_score > 0.5:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # 判断一致性
                consensus = (ml_prob > 0.5 and factor_score > 0.5) or (ml_prob <= 0.5 and factor_score <= 0.5)
                
                result = {
                    "stock_code": stock_code,
                    "stock_name": stock_info[stock_code],
                    "final_score": final_score,
                    "ml_probability": ml_prob,
                    "factor_score": factor_score,
                    "confidence_level": confidence,
                    "reason": reason,
                    "consensus": consensus,
                    "details": {
                        "ml_prediction": ml_predictions[stock_code]['prediction'],
                        "factor_rank": factor_scores[stock_code]['rank']
                    }
                }
                
                results.append(result)
        
        # 按最终得分排序
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # 添加排名
        for i, result in enumerate(results[:top_n]):
            result['rank'] = i + 1
        
        # 输出结果
        print(f"\n推荐结果 (Top {top_n}):")
        print("-" * 80)
        
        for result in results[:top_n]:
            print(f"{result['rank']}. {result['stock_name']} ({result['stock_code']})")
            print(f"   最终得分: {result['final_score']:.3f}")
            print(f"   ML概率: {result['ml_probability']:.2f}, 因子得分: {result['factor_score']:.2f}")
            print(f"   置信度: {result['confidence_level']}, 一致性: {'是' if result['consensus'] else '否'}")
            print(f"   推荐理由: {result['reason']}")
            print()
        
        # 统计信息
        consensus_count = sum(1 for r in results if r['consensus'])
        avg_ml_prob = sum(r['ml_probability'] for r in results) / len(results)
        avg_factor_score = sum(r['factor_score'] for r in results) / len(results)
        
        print(f"统计信息:")
        print(f"- 总股票数: {len(results)}")
        print(f"- 推荐数量: {min(top_n, len(results))}")
        print(f"- 一致性比例: {consensus_count/len(results):.1%} ({consensus_count}/{len(results)})")
        print(f"- 平均ML概率: {avg_ml_prob:.3f}")
        print(f"- 平均因子得分: {avg_factor_score:.3f}")
        
        # 保存结果到JSON文件
        output_data = {
            "method": method_name,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "top_n": top_n,
                "test_mode": True
            },
            "recommendations": results[:top_n],
            "summary": {
                "total_stocks": len(results),
                "recommended_count": min(top_n, len(results)),
                "consensus_ratio": consensus_count/len(results),
                "avg_ml_probability": avg_ml_prob,
                "avg_factor_score": avg_factor_score
            }
        }
        
        # 确保results目录存在
        os.makedirs("results", exist_ok=True)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/test_fusion_{method_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {filename}")
        
        return results[:top_n]
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    主函数：测试所有融合方法
    """
    print("增强版融合策略测试")
    print("=" * 60)
    
    # 测试不同的融合方法
    methods = [
        "weighted_average",
        "filter_first", 
        "consensus_boost"
    ]
    
    all_results = {}
    
    for method in methods:
        results = test_fusion_method(method, top_n=5)
        if results:
            all_results[method] = results
    
    # 比较结果
    print(f"\n{'='*60}")
    print("方法比较")
    print(f"{'='*60}")
    
    if all_results:
        print("\n各方法Top 3推荐:")
        for method, results in all_results.items():
            print(f"\n{method}:")
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result['stock_name']} - {result['final_score']:.3f}")
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print("详细结果已保存到 results/ 目录")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()