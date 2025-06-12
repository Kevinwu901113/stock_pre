#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版卖出信号判断模块测试脚本
用于测试和演示卖出信号判断功能
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random
from enhanced_sell_signal import EnhancedSellSignal, SellSignalType, SellAction

# 模拟数据生成器
class MockDataGenerator:
    """模拟数据生成器，用于测试卖出信号判断模块"""
    
    def __init__(self, stock_count=20):
        self.stock_count = stock_count
        self.stock_pool = [
            {"code": "600519", "name": "贵州茅台"},
            {"code": "000001", "name": "平安银行"},
            {"code": "600036", "name": "招商银行"},
            {"code": "601318", "name": "中国平安"},
            {"code": "000333", "name": "美的集团"},
            {"code": "600276", "name": "恒瑞医药"},
            {"code": "601166", "name": "兴业银行"},
            {"code": "600887", "name": "伊利股份"},
            {"code": "000858", "name": "五粮液"},
            {"code": "002415", "name": "海康威视"},
            {"code": "601888", "name": "中国中免"},
            {"code": "600030", "name": "中信证券"},
            {"code": "601398", "name": "工商银行"},
            {"code": "000651", "name": "格力电器"},
            {"code": "600000", "name": "浦发银行"},
            {"code": "601288", "name": "农业银行"},
            {"code": "600585", "name": "海螺水泥"},
            {"code": "601668", "name": "中国建筑"},
            {"code": "601988", "name": "中国银行"},
            {"code": "600028", "name": "中国石化"},
            {"code": "601857", "name": "中国石油"},
            {"code": "601328", "name": "交通银行"},
            {"code": "601088", "name": "中国神华"},
            {"code": "600019", "name": "宝钢股份"},
            {"code": "601628", "name": "中国人寿"},
            {"code": "601601", "name": "中国太保"},
            {"code": "600104", "name": "上汽集团"},
            {"code": "600050", "name": "中国联通"},
            {"code": "601766", "name": "中国中车"},
            {"code": "601186", "name": "中国铁建"}
        ]
    
    def generate_mock_recommendations(self, count=None):
        """生成模拟推荐列表"""
        if count is None:
            count = self.stock_count
        
        # 随机选择股票
        selected_stocks = random.sample(self.stock_pool, min(count, len(self.stock_pool)))
        
        recommendations = []
        for i, stock in enumerate(selected_stocks):
            # 生成模拟的ML概率和因子得分
            ml_prob = round(random.uniform(0.6, 0.95), 2)
            factor_score = round(random.uniform(70, 95), 1)
            
            # 计算融合得分
            fusion_score = round(ml_prob * 0.6 + factor_score / 100 * 0.4, 3)
            
            # 生成推荐理由
            reasons = [
                "基本面良好，业绩稳定增长",
                "技术面突破，量价配合",
                "行业龙头，具有较强竞争力",
                "估值合理，具有安全边际",
                "政策利好，受益于行业发展"
            ]
            reason = random.choice(reasons)
            
            recommendations.append({
                "stock_code": stock["code"],
                "stock_name": stock["name"],
                "ml_probability": ml_prob,
                "factor_score": factor_score,
                "final_score": fusion_score,
                "rank": i + 1,
                "recommendation_reason": reason,
                "recommendation_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            })
        
        return recommendations
    
    def generate_mock_market_data(self, stock_codes):
        """生成模拟市场数据"""
        market_data = {}
        
        # 生成不同场景的股票
        scenarios = [
            "big_gain",      # 大幅上涨
            "small_gain",    # 小幅上涨
            "flat",         # 基本平稳
            "small_loss",    # 小幅下跌
            "big_loss",      # 大幅下跌
            "volume_spike",  # 成交量放大
            "fund_outflow",  # 资金流出
            "sentiment_bad"  # 情绪转空
        ]
        
        # 为每只股票分配场景
        stock_scenarios = {}
        for i, code in enumerate(stock_codes):
            scenario = scenarios[i % len(scenarios)]
            stock_scenarios[code] = scenario
        
        # 根据场景生成数据
        for code in stock_codes:
            scenario = stock_scenarios[code]
            
            # 基础数据
            yesterday_close = round(random.uniform(10, 100), 2)
            
            # 根据场景设置涨跌幅
            if scenario == "big_gain":
                change_pct = round(random.uniform(3.5, 7.0), 2)
            elif scenario == "small_gain":
                change_pct = round(random.uniform(0.5, 2.5), 2)
            elif scenario == "flat":
                change_pct = round(random.uniform(-0.5, 0.5), 2)
            elif scenario == "small_loss":
                change_pct = round(random.uniform(-2.5, -0.5), 2)
            elif scenario == "big_loss":
                change_pct = round(random.uniform(-7.0, -3.5), 2)
            else:
                change_pct = round(random.uniform(-3.0, 3.0), 2)
            
            current_price = round(yesterday_close * (1 + change_pct / 100), 2)
            
            # 成交量和振幅
            base_volume = random.randint(1000000, 10000000)
            if scenario == "volume_spike":
                volume = base_volume * random.randint(3, 5)
                amplitude = round(random.uniform(8.0, 12.0), 2)
            else:
                volume = base_volume
                amplitude = round(abs(change_pct) * 1.5, 2)
            
            # 生成市场数据
            market_data[code] = {
                "current_price": current_price,
                "yesterday_close": yesterday_close,
                "change_percent": change_pct,
                "volume": volume,
                "turnover": volume * current_price,
                "amplitude": amplitude,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scenario": scenario  # 添加场景标记，方便验证
            }
        
        return market_data
    
    def generate_mock_fund_flow_data(self, stock_code):
        """生成模拟资金流向数据"""
        # 获取股票对应的场景
        scenario = "normal"
        
        # 根据场景生成资金流向
        if scenario == "fund_outflow":
            main_inflow = -random.randint(50000000, 100000000)  # 主力大幅流出
            retail_inflow = -random.randint(10000000, 30000000)  # 散户也流出
        elif scenario == "big_loss" or scenario == "small_loss":
            main_inflow = -random.randint(20000000, 50000000)  # 主力流出
            retail_inflow = random.randint(-20000000, 10000000)  # 散户可能流出也可能流入
        elif scenario == "big_gain":
            main_inflow = random.randint(30000000, 80000000)  # 主力流入
            retail_inflow = random.randint(10000000, 30000000)  # 散户流入
        else:
            main_inflow = random.randint(-30000000, 30000000)  # 主力流入流出不确定
            retail_inflow = random.randint(-20000000, 20000000)  # 散户流入流出不确定
        
        # 创建DataFrame
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
        data = []
        
        for i, date in enumerate(dates):
            if i == 0:  # 今日
                data.append({
                    "日期": date,
                    "主力净流入": main_inflow,
                    "散户净流入": retail_inflow,
                    "总流入": main_inflow + retail_inflow
                })
            else:  # 历史数据
                hist_main = random.randint(-40000000, 40000000)
                hist_retail = random.randint(-20000000, 20000000)
                data.append({
                    "日期": date,
                    "主力净流入": hist_main,
                    "散户净流入": hist_retail,
                    "总流入": hist_main + hist_retail
                })
        
        return pd.DataFrame(data)
    
    def generate_mock_sentiment_data(self):
        """生成模拟情绪数据"""
        # 市场整体情绪
        market_sentiment = random.randint(30, 70)
        fear_ratio = round(random.uniform(0.3, 0.7), 2)
        
        # 个股情绪
        stocks_sentiment = {}
        for stock in self.stock_pool:
            code = stock["code"]
            # 根据股票场景设置情绪
            if code in ["600519", "000001", "600036"]:  # 特定股票情绪较差
                sentiment_score = random.randint(15, 30)
            else:
                sentiment_score = random.randint(30, 80)
            
            stocks_sentiment[code] = {
                "sentiment_score": sentiment_score,
                "positive_ratio": round(sentiment_score / 100, 2),
                "negative_ratio": round(1 - sentiment_score / 100, 2)
            }
        
        return {
            "market_sentiment": market_sentiment,
            "fear_ratio": fear_ratio,
            "stocks": stocks_sentiment
        }

# 模拟数据获取器
class MockDataFetcher:
    """模拟数据获取器，替代真实的DataFetcher"""
    
    def __init__(self):
        self.data_generator = MockDataGenerator()
        self.market_data_cache = {}
        self.fund_flow_cache = {}
        self.sentiment_data = self.data_generator.generate_mock_sentiment_data()
    
    def get_stock_realtime_data(self, stock_codes):
        """获取股票实时数据"""
        if not self.market_data_cache:
            self.market_data_cache = self.data_generator.generate_mock_market_data(stock_codes)
        
        result = {}
        for code in stock_codes:
            if code in self.market_data_cache:
                data = self.market_data_cache[code]
                result[code] = {
                    "price": data["current_price"],
                    "volume": data["volume"],
                    "turnover": data["turnover"],
                    "amplitude": data["amplitude"]
                }
        
        return result
    
    def get_stock_history_data(self, stock_code, period=5):
        """获取股票历史数据"""
        # 生成模拟历史数据
        data = []
        base_price = random.uniform(10, 100)
        
        for i in range(period):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            change = random.uniform(-0.05, 0.05)
            close = round(base_price * (1 + change), 2)
            open_price = round(close * (1 + random.uniform(-0.02, 0.02)), 2)
            high = round(max(open_price, close) * (1 + random.uniform(0, 0.03)), 2)
            low = round(min(open_price, close) * (1 - random.uniform(0, 0.03)), 2)
            volume = random.randint(1000000, 10000000)
            
            data.append({
                "日期": date,
                "开盘": open_price,
                "收盘": close,
                "最高": high,
                "最低": low,
                "成交量": volume
            })
            
            base_price = close
        
        return pd.DataFrame(data)
    
    def get_capital_flow_data(self, stock_code, period=3):
        """获取资金流向数据"""
        if stock_code not in self.fund_flow_cache:
            self.fund_flow_cache[stock_code] = self.data_generator.generate_mock_fund_flow_data(stock_code)
        
        return self.fund_flow_cache[stock_code]
    
    def get_market_sentiment_data(self):
        """获取市场情绪数据"""
        return self.sentiment_data

# 测试类
class SellSignalTester:
    """卖出信号测试器"""
    
    def __init__(self, config_file=None):
        self.mock_data_generator = MockDataGenerator()
        self.sell_analyzer = EnhancedSellSignal(config_file)
        
        # 替换数据获取器为模拟数据获取器
        self.sell_analyzer.data_fetcher = MockDataFetcher()
    
    def generate_test_recommendations(self, count=20):
        """生成测试用的推荐列表"""
        recommendations = self.mock_data_generator.generate_mock_recommendations(count)
        
        # 保存推荐列表
        os.makedirs("results", exist_ok=True)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        filename = f"results/fusion_results_{yesterday}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        
        print(f"测试推荐列表已保存: {filename}")
        return recommendations
    
    def run_test(self, recommendations=None):
        """运行测试"""
        if recommendations is None:
            recommendations = self.generate_test_recommendations()
        
        # 执行卖出信号分析
        results = self.sell_analyzer.analyze_sell_signals()
        
        # 保存结果
        filename = self.sell_analyzer.save_results(results)
        
        return results, filename
    
    def analyze_test_results(self, results):
        """分析测试结果"""
        decisions = results['decisions']
        summary = results['summary']
        
        # 按操作类型分组
        action_groups = {}
        for decision in decisions:
            action = decision['action']
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append(decision)
        
        # 按信号类型分组
        signal_groups = {}
        for decision in decisions:
            signal_type = decision.get('signal_type')
            if signal_type:
                if signal_type not in signal_groups:
                    signal_groups[signal_type] = []
                signal_groups[signal_type].append(decision)
        
        # 打印分析结果
        print("\n📊 测试结果分析")
        print("=" * 60)
        
        print(f"\n总计股票: {summary['total_stocks']}只")
        print(f"平均涨跌幅: {summary['return_stats']['avg_return']}%")
        
        print(f"\n🎯 操作建议分布:")
        for action, stocks in action_groups.items():
            print(f"  {action}: {len(stocks)}只 ({len(stocks)/len(decisions):.1%})")
        
        print(f"\n⚠️ 信号类型分布:")
        for signal, stocks in signal_groups.items():
            print(f"  {signal}: {len(stocks)}只 ({len(stocks)/len(decisions):.1%})")
        
        # 验证卖出信号的准确性
        print("\n🔍 卖出信号验证:")
        
        # 检查止盈止损信号
        profit_taking = signal_groups.get(SellSignalType.PROFIT_TAKING.value, [])
        if profit_taking:
            avg_gain = np.mean([d.get('change_percent', 0) for d in profit_taking])
            print(f"  止盈信号平均涨幅: {avg_gain:.2f}%")
        
        stop_loss = signal_groups.get(SellSignalType.STOP_LOSS.value, [])
        if stop_loss:
            avg_loss = np.mean([d.get('change_percent', 0) for d in stop_loss])
            print(f"  止损信号平均跌幅: {avg_loss:.2f}%")
        
        # 检查紧急程度分布
        urgency_counts = summary['urgency_distribution']
        print(f"\n🔥 紧急程度分布:")
        for urgency, count in urgency_counts.items():
            print(f"  {urgency}: {count}只 ({count/len(decisions):.1%})")
        
        return action_groups, signal_groups

def main():
    """主函数"""
    print("🧪 增强版卖出信号判断模块测试")
    print("=" * 60)
    
    # 初始化测试器
    config_file = "sell_signal_config.json"
    tester = SellSignalTester(config_file)
    
    # 生成测试数据
    print("\n📋 生成测试数据...")
    recommendations = tester.generate_test_recommendations(20)
    print(f"已生成{len(recommendations)}只测试股票")
    
    # 运行测试
    print("\n🚀 执行卖出信号分析...")
    results, filename = tester.run_test(recommendations)
    
    # 显示测试结果
    summary = results['summary']
    decisions = results['decisions']
    
    print(f"\n📊 分析汇总 ({summary['analysis_time']})")
    print(f"总计股票: {summary['total_stocks']}只")
    
    if summary['total_stocks'] > 0:
        print(f"\n📈 收益统计:")
        stats = summary['return_stats']
        print(f"  平均涨跌幅: {stats['avg_return']}%")
        print(f"  最大涨幅: {stats['max_return']}%")
        print(f"  最大跌幅: {stats['min_return']}%")
        print(f"  上涨股票: {stats['positive_count']}只 ({stats['positive_ratio']:.1%})")
        print(f"  下跌股票: {stats['negative_count']}只")
        
        print(f"\n🎯 操作建议分布:")
        for action, count in summary['action_distribution'].items():
            print(f"  {action}: {count}只")
        
        print(f"\n⚠️ 信号类型分布:")
        for signal, count in summary['signal_distribution'].items():
            print(f"  {signal}: {count}只")
        
        print(f"\n📋 详细决策 (前5只):")
        print("-" * 80)
        for i, decision in enumerate(decisions[:5]):
            urgency_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(decision.get('urgency'), "")
            print(f"{i+1:2d}. {decision['stock_name']}({decision['stock_code']}) {urgency_icon}")
            print(f"     涨跌幅: {decision.get('change_percent', 0):+.2f}% | 操作: {decision['action']}")
            print(f"     信号: {decision.get('signal_type', 'N/A')} | 理由: {decision['reason']}")
            print()
    
    # 分析测试结果
    action_groups, signal_groups = tester.analyze_test_results(results)
    
    print(f"\n💾 详细结果已保存: {filename}")
    print("\n" + "=" * 60)
    print("🎯 卖出信号测试完成！")

if __name__ == "__main__":
    main()