#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术因子演示脚本
展示如何使用扩展后的特征提取器计算各种技术因子
"""

import pandas as pd
import numpy as np
from feature_extractor import FeatureExtractor
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sample_data(stock_code: str = "000001", days: int = 60) -> dict:
    """
    生成示例股票数据用于测试
    """
    # 生成日期序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 生成模拟价格数据
    np.random.seed(42)  # 固定随机种子以便复现
    base_price = 10.0
    price_changes = np.random.normal(0, 0.02, len(date_range))  # 2%的日波动
    
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.1))  # 确保价格不为负
    
    # 生成OHLC数据
    hist_data = []
    for i, (date, close_price) in enumerate(zip(date_range, prices)):
        # 生成开高低收数据
        daily_volatility = np.random.uniform(0.005, 0.03)  # 0.5%-3%的日内波动
        
        high = close_price * (1 + daily_volatility)
        low = close_price * (1 - daily_volatility)
        open_price = close_price * (1 + np.random.uniform(-0.01, 0.01))
        
        # 生成成交量（与价格变化相关）
        volume_base = 1000000  # 100万股基础成交量
        price_change_pct = abs(price_changes[i]) if i > 0 else 0
        volume = volume_base * (1 + price_change_pct * 10) * np.random.uniform(0.5, 2.0)
        
        hist_data.append({
            '日期': date.strftime('%Y-%m-%d'),
            '开盘': round(open_price, 2),
            '最高': round(high, 2),
            '最低': round(low, 2),
            '收盘': round(close_price, 2),
            '成交量': int(volume)
        })
    
    hist_df = pd.DataFrame(hist_data)
    
    # 生成实时数据
    current_price = prices[-1]
    yesterday_price = prices[-2] if len(prices) > 1 else current_price
    change_pct = (current_price / yesterday_price - 1) * 100
    
    realtime_data = {
        'price': round(current_price, 2),
        'change_pct': round(change_pct, 2),
        'amplitude': round(abs(change_pct) * 1.5, 2),
        'volume': int(hist_data[-1]['成交量'] * 1.2),
        'turnover': np.random.uniform(50000000, 500000000)  # 5千万到5亿的成交额
    }
    
    # 生成资金流向数据
    capital_flow_data = {
        'main_net_inflow': np.random.uniform(-50000000, 100000000),  # -5千万到1亿
        'main_net_inflow_pct': np.random.uniform(-5, 8),  # -5%到8%
        'large_net_inflow': np.random.uniform(-30000000, 60000000),
        'super_large_net_inflow': np.random.uniform(-20000000, 40000000)
    }
    
    # 生成市场情绪数据
    market_sentiment = {
        'up_ratio': np.random.uniform(0.3, 0.7),  # 30%-70%的上涨比例
        'limit_up_count': np.random.randint(0, 50)  # 0-50只涨停股票
    }
    
    # 生成行业表现数据
    market_data = {
        'sector_performance': {
            '主板': np.random.uniform(-3, 5),
            '创业板': np.random.uniform(-5, 8),
            '沪市主板': np.random.uniform(-2, 4),
            '科创板': np.random.uniform(-6, 10),
            '其他': np.random.uniform(-3, 3)
        }
    }
    
    return {
        'history': hist_df,
        'realtime': realtime_data,
        'capital_flow': capital_flow_data,
        'news_sentiment': np.random.uniform(0.2, 0.8),  # 新闻情绪
        'market_sentiment': market_sentiment,
        'market_data': market_data
    }

def demo_basic_usage():
    """
    演示基本用法
    """
    logger.info("=== 基本用法演示 ===")
    
    # 初始化特征提取器
    extractor = FeatureExtractor(
        config_path="config.yaml",
        factor_strategy="default",
        time_period="medium_term",
        factor_enable_config_path="factor_enable_config.yaml"
    )
    
    # 生成示例数据
    stock_data = generate_sample_data("000001", days=60)
    
    # 提取特征
    features = extractor.extract_all_features(stock_data, stock_code="000001")
    
    # 显示结果
    logger.info(f"提取到 {len(features)} 个因子:")
    for factor_name, factor_value in sorted(features.items()):
        logger.info(f"  {factor_name}: {factor_value:.4f}")
    
    return features

def demo_factor_categories():
    """
    演示不同类别的因子
    """
    logger.info("\n=== 因子分类演示 ===")
    
    extractor = FeatureExtractor()
    stock_data = generate_sample_data("000001", days=60)
    features = extractor.extract_all_features(stock_data, stock_code="000001")
    
    # 按类别分组显示因子
    factor_categories = {
        '动量因子': ['momentum_5d', 'momentum_10d', 'momentum_20d', 'momentum_5d_new', 'rsi'],
        '成交量因子': ['volume_ratio', 'volume_spike', 'turnover_rate', 'volume_ratio_new'],
        '技术指标': ['macd', 'macd_diff', 'bollinger_position', 'kdj_golden_cross', 'ma_slope_5d', 'ma_slope_10d'],
        '资金流向': ['main_inflow_score', 'large_inflow_score', 'capital_strength', 'main_capital_inflow'],
        '市场状态': ['limit_up_yesterday', 'sector_performance'],
        '风险因子': ['volatility_20d', 'price_stability']
    }
    
    for category, factor_names in factor_categories.items():
        logger.info(f"\n{category}:")
        for factor_name in factor_names:
            if factor_name in features:
                logger.info(f"  {factor_name}: {features[factor_name]:.4f}")
            else:
                logger.info(f"  {factor_name}: 未启用或计算失败")

def demo_factor_configuration():
    """
    演示因子配置功能
    """
    logger.info("\n=== 因子配置演示 ===")
    
    # 测试不同的配置
    configs = [
        ("default", "medium_term"),
        ("momentum_focused", "short_term"),
        ("conservative", "long_term")
    ]
    
    stock_data = generate_sample_data("000001", days=60)
    
    for strategy, period in configs:
        try:
            extractor = FeatureExtractor(
                factor_strategy=strategy,
                time_period=period
            )
            features = extractor.extract_all_features(stock_data, stock_code="000001")
            logger.info(f"\n策略: {strategy}, 周期: {period} - 提取到 {len(features)} 个因子")
            
            # 显示几个关键因子
            key_factors = ['momentum_5d_new', 'macd_diff', 'kdj_golden_cross', 'sector_performance']
            for factor in key_factors:
                if factor in features:
                    logger.info(f"  {factor}: {features[factor]:.4f}")
                    
        except Exception as e:
            logger.error(f"配置 {strategy}-{period} 测试失败: {e}")

def demo_batch_processing():
    """
    演示批量处理
    """
    logger.info("\n=== 批量处理演示 ===")
    
    extractor = FeatureExtractor()
    
    # 生成多只股票的数据
    stock_codes = ["000001", "000002", "600000", "300001"]
    all_stock_data = {}
    
    for code in stock_codes:
        all_stock_data[code] = generate_sample_data(code, days=60)
    
    # 批量提取特征
    all_features = extractor.batch_extract_features(all_stock_data)
    
    logger.info(f"批量处理完成，共处理 {len(all_features)} 只股票")
    
    # 显示每只股票的关键因子
    key_factors = ['momentum_5d_new', 'kdj_golden_cross', 'sector_performance', 'main_capital_inflow']
    
    for stock_code, features in all_features.items():
        logger.info(f"\n股票 {stock_code}:")
        for factor in key_factors:
            if factor in features:
                logger.info(f"  {factor}: {features[factor]:.4f}")

def demo_new_factors():
    """
    重点演示新增的技术因子
    """
    logger.info("\n=== 新增技术因子演示 ===")
    
    extractor = FeatureExtractor()
    stock_data = generate_sample_data("000001", days=60)
    features = extractor.extract_all_features(stock_data, stock_code="000001")
    
    # 重点展示新增的因子
    new_factors = {
        'momentum_5d_new': '近5日涨跌幅（标准化）',
        'macd_diff': 'MACD差值（MACD线-信号线）',
        'kdj_golden_cross': 'KDJ金叉信号',
        'ma_slope_5d': '5日均线斜率',
        'ma_slope_10d': '10日均线斜率',
        'volume_ratio_new': '量比（当前/近期平均）',
        'limit_up_yesterday': '前一日涨停状态',
        'sector_performance': '所属行业表现',
        'main_capital_inflow': '主力资金净流入（标准化）'
    }
    
    logger.info("新增技术因子详情:")
    for factor_name, description in new_factors.items():
        if factor_name in features:
            value = features[factor_name]
            logger.info(f"  {factor_name} ({description}): {value:.4f}")
            
            # 提供解释
            if factor_name == 'momentum_5d_new':
                if value > 70:
                    interpretation = "强势上涨"
                elif value > 50:
                    interpretation = "温和上涨"
                elif value > 30:
                    interpretation = "温和下跌"
                else:
                    interpretation = "明显下跌"
                logger.info(f"    解释: {interpretation}")
                
            elif factor_name == 'kdj_golden_cross':
                if value > 80:
                    interpretation = "强烈金叉信号"
                elif value > 50:
                    interpretation = "金叉信号"
                else:
                    interpretation = "无金叉或死叉"
                logger.info(f"    解释: {interpretation}")
                
            elif factor_name == 'limit_up_yesterday':
                if value > 90:
                    interpretation = "前日涨停"
                elif value > 50:
                    interpretation = "前日大涨"
                elif value > 20:
                    interpretation = "前日上涨"
                else:
                    interpretation = "前日未上涨"
                logger.info(f"    解释: {interpretation}")

def main():
    """
    主函数
    """
    logger.info("技术因子演示程序启动")
    
    try:
        # 运行各种演示
        demo_basic_usage()
        demo_factor_categories()
        demo_new_factors()
        demo_factor_configuration()
        demo_batch_processing()
        
        logger.info("\n=== 演示完成 ===")
        logger.info("\n使用说明:")
        logger.info("1. 修改 factor_enable_config.yaml 可以启用/禁用特定因子")
        logger.info("2. 修改 factor_config.yaml 可以调整因子权重")
        logger.info("3. 修改 config.yaml 可以调整技术指标参数")
        logger.info("4. 支持 TA-Lib 和 pandas-ta 库，未安装时自动使用自定义实现")
        logger.info("5. 所有因子都已标准化到 0-100 区间，便于后续打分使用")
        
    except Exception as e:
        logger.error(f"演示程序执行失败: {e}")
        raise

if __name__ == "__main__":
    main()