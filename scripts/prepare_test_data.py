#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import requests
from typing import List, Dict, Any

class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, data_dir="data/csv"):
        self.data_dir = data_dir
        self.ensure_data_dir()
        
        # 真实股票列表
        self.real_stocks = [
            {"code": "000001", "name": "平安银行", "industry": "银行", "sector": "金融"},
            {"code": "600036", "name": "招商银行", "industry": "银行", "sector": "金融"},
            {"code": "000002", "name": "万科A", "industry": "房地产开发", "sector": "房地产"},
            {"code": "600519", "name": "贵州茅台", "industry": "白酒", "sector": "食品饮料"},
            {"code": "000858", "name": "五粮液", "industry": "白酒", "sector": "食品饮料"},
            {"code": "600000", "name": "浦发银行", "industry": "银行", "sector": "金融"},
            {"code": "000858", "name": "五粮液", "industry": "白酒", "sector": "食品饮料"},
            {"code": "002415", "name": "海康威视", "industry": "安防设备", "sector": "电子"},
            {"code": "300059", "name": "东方财富", "industry": "证券", "sector": "金融"},
            {"code": "000725", "name": "京东方A", "industry": "显示器件", "sector": "电子"}
        ]
        
    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "backup"), exist_ok=True)
        
    def generate_stock_basic_info(self) -> pd.DataFrame:
        """生成股票基础信息"""
        print("📊 生成股票基础信息...")
        
        stocks_data = []
        for stock in self.real_stocks:
            stock_info = {
                "code": stock["code"],
                "name": stock["name"],
                "market": "A",
                "industry": stock["industry"],
                "sector": stock["sector"],
                "list_date": self._generate_list_date(),
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            stocks_data.append(stock_info)
            
        stocks_df = pd.DataFrame(stocks_data)
        
        # 保存到CSV
        stocks_file = os.path.join(self.data_dir, "stocks.csv")
        stocks_df.to_csv(stocks_file, index=False, encoding="utf-8")
        
        print(f"✅ 股票基础信息已保存: {stocks_file} ({len(stocks_data)} 条记录)")
        return stocks_df
        
    def generate_stock_prices(self, days=365) -> pd.DataFrame:
        """生成股票价格数据"""
        print(f"📈 生成股票价格数据 ({days} 天)...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        all_price_data = []
        
        for stock in self.real_stocks:
            stock_code = stock["code"]
            print(f"   生成 {stock_code} - {stock['name']} 的价格数据...")
            
            # 生成该股票的价格数据
            stock_prices = self._generate_stock_price_series(
                stock_code, start_date, end_date, stock["industry"]
            )
            all_price_data.extend(stock_prices)
            
        price_df = pd.DataFrame(all_price_data)
        
        # 保存到CSV
        prices_file = os.path.join(self.data_dir, "stock_prices.csv")
        price_df.to_csv(prices_file, index=False, encoding="utf-8")
        
        print(f"✅ 股票价格数据已保存: {prices_file} ({len(all_price_data)} 条记录)")
        return price_df
        
    def generate_stock_fundamentals(self) -> pd.DataFrame:
        """生成股票基本面数据"""
        print("📊 生成股票基本面数据...")
        
        fundamentals_data = []
        
        for stock in self.real_stocks:
            stock_code = stock["code"]
            
            # 生成最近12个月的基本面数据
            for i in range(12):
                date = datetime.now().date() - timedelta(days=30*i)
                
                fundamental = {
                    "stock_code": stock_code,
                    "date": date.strftime("%Y-%m-%d"),
                    "pe_ratio": self._generate_pe_ratio(stock["industry"]),
                    "pb_ratio": self._generate_pb_ratio(stock["industry"]),
                    "market_cap": self._generate_market_cap(stock["industry"]),
                    "total_share": np.random.uniform(1e9, 1e10),  # 总股本
                    "float_share": np.random.uniform(5e8, 8e9),   # 流通股本
                    "revenue": self._generate_revenue(stock["industry"]),
                    "net_profit": self._generate_net_profit(stock["industry"]),
                    "roe": np.random.uniform(0.05, 0.25),  # ROE
                    "roa": np.random.uniform(0.02, 0.15),  # ROA
                    "debt_ratio": np.random.uniform(0.2, 0.7),  # 资产负债率
                    "created_at": datetime.now().isoformat()
                }
                fundamentals_data.append(fundamental)
                
        fundamentals_df = pd.DataFrame(fundamentals_data)
        
        # 保存到CSV
        fundamentals_file = os.path.join(self.data_dir, "stock_fundamentals.csv")
        fundamentals_df.to_csv(fundamentals_file, index=False, encoding="utf-8")
        
        print(f"✅ 股票基本面数据已保存: {fundamentals_file} ({len(fundamentals_data)} 条记录)")
        return fundamentals_df
        
    def generate_technical_indicators(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """生成技术指标数据"""
        print("📊 生成技术指标数据...")
        
        indicators_data = []
        
        for stock_code in price_df['stock_code'].unique():
            stock_prices = price_df[price_df['stock_code'] == stock_code].sort_values('date')
            
            if len(stock_prices) < 30:  # 需要足够的数据计算指标
                continue
                
            # 计算技术指标
            closes = stock_prices['close'].values
            highs = stock_prices['high'].values
            lows = stock_prices['low'].values
            volumes = stock_prices['volume'].values
            
            # 移动平均线
            ma5 = self._calculate_ma(closes, 5)
            ma10 = self._calculate_ma(closes, 10)
            ma20 = self._calculate_ma(closes, 20)
            ma60 = self._calculate_ma(closes, 60)
            
            # RSI
            rsi = self._calculate_rsi(closes, 14)
            
            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(closes)
            
            # 布林带
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes, 20)
            
            # KDJ
            k, d, j = self._calculate_kdj(highs, lows, closes, 9)
            
            for i, row in stock_prices.iterrows():
                idx = stock_prices.index.get_loc(i)
                
                indicator = {
                    "stock_code": stock_code,
                    "date": row['date'],
                    "ma5": ma5[idx] if idx < len(ma5) else None,
                    "ma10": ma10[idx] if idx < len(ma10) else None,
                    "ma20": ma20[idx] if idx < len(ma20) else None,
                    "ma60": ma60[idx] if idx < len(ma60) else None,
                    "rsi": rsi[idx] if idx < len(rsi) else None,
                    "macd": macd[idx] if idx < len(macd) else None,
                    "macd_signal": macd_signal[idx] if idx < len(macd_signal) else None,
                    "macd_hist": macd_hist[idx] if idx < len(macd_hist) else None,
                    "bb_upper": bb_upper[idx] if idx < len(bb_upper) else None,
                    "bb_middle": bb_middle[idx] if idx < len(bb_middle) else None,
                    "bb_lower": bb_lower[idx] if idx < len(bb_lower) else None,
                    "kdj_k": k[idx] if idx < len(k) else None,
                    "kdj_d": d[idx] if idx < len(d) else None,
                    "kdj_j": j[idx] if idx < len(j) else None,
                    "created_at": datetime.now().isoformat()
                }
                indicators_data.append(indicator)
                
        indicators_df = pd.DataFrame(indicators_data)
        
        # 保存到CSV
        indicators_file = os.path.join(self.data_dir, "technical_indicators.csv")
        indicators_df.to_csv(indicators_file, index=False, encoding="utf-8")
        
        print(f"✅ 技术指标数据已保存: {indicators_file} ({len(indicators_data)} 条记录)")
        return indicators_df
        
    def generate_sample_recommendations(self) -> pd.DataFrame:
        """生成示例推荐数据"""
        print("💡 生成示例推荐数据...")
        
        recommendations_data = []
        
        # 生成最近7天的推荐数据
        for days_ago in range(7):
            date = datetime.now().date() - timedelta(days=days_ago)
            
            # 每天生成3-8条推荐
            daily_count = np.random.randint(3, 9)
            
            for _ in range(daily_count):
                stock = np.random.choice(self.real_stocks)
                signal_type = np.random.choice(['buy', 'sell'], p=[0.7, 0.3])  # 买入推荐更多
                
                # 模拟当前价格
                current_price = self._generate_realistic_price(stock["industry"])
                
                if signal_type == 'buy':
                    target_price = current_price * np.random.uniform(1.05, 1.20)  # 5-20%涨幅
                    stop_loss = current_price * np.random.uniform(0.90, 0.95)    # 5-10%止损
                else:
                    target_price = current_price * np.random.uniform(0.85, 0.95)  # 5-15%跌幅
                    stop_loss = current_price * np.random.uniform(1.05, 1.10)    # 5-10%止损
                    
                recommendation = {
                    "id": f"rec_{date.strftime('%Y%m%d')}_{len(recommendations_data)+1:03d}",
                    "stock_code": stock["code"],
                    "stock_name": stock["name"],
                    "signal": signal_type,
                    "current_price": round(current_price, 2),
                    "target_price": round(target_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "confidence": np.random.uniform(0.6, 0.95),
                    "expected_return": abs(target_price - current_price) / current_price,
                    "holding_period": np.random.randint(5, 30),  # 持有天数
                    "reason": self._generate_recommendation_reason(signal_type, stock["industry"]),
                    "strategy_name": np.random.choice(["MA均线策略", "RSI策略", "MACD策略", "综合技术策略"]),
                    "created_at": datetime.combine(date, datetime.min.time()).isoformat(),
                    "updated_at": datetime.combine(date, datetime.min.time()).isoformat()
                }
                recommendations_data.append(recommendation)
                
        recommendations_df = pd.DataFrame(recommendations_data)
        
        # 保存到CSV
        recommendations_file = os.path.join(self.data_dir, "recommendations.csv")
        recommendations_df.to_csv(recommendations_file, index=False, encoding="utf-8")
        
        print(f"✅ 示例推荐数据已保存: {recommendations_file} ({len(recommendations_data)} 条记录)")
        return recommendations_df
        
    def _generate_list_date(self) -> str:
        """生成上市日期"""
        # 随机生成1990-2020年间的上市日期
        start_date = datetime(1990, 1, 1)
        end_date = datetime(2020, 12, 31)
        
        random_date = start_date + timedelta(
            days=np.random.randint(0, (end_date - start_date).days)
        )
        
        return random_date.strftime("%Y-%m-%d")
        
    def _generate_stock_price_series(self, stock_code: str, start_date, end_date, industry: str) -> List[Dict]:
        """生成单只股票的价格序列"""
        prices = []
        
        # 根据行业设置基础价格范围
        industry_price_ranges = {
            "银行": (8, 25),
            "白酒": (100, 300),
            "房地产开发": (5, 30),
            "安防设备": (20, 60),
            "证券": (10, 40),
            "显示器件": (3, 15)
        }
        
        price_range = industry_price_ranges.get(industry, (10, 50))
        base_price = np.random.uniform(*price_range)
        
        current_date = start_date
        current_price = base_price
        
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            # 生成日内价格波动
            daily_change = np.random.normal(0, 0.02)  # 2%的日波动
            trend_factor = np.random.normal(0, 0.001)  # 长期趋势
            
            # 计算开盘价（基于前一日收盘价）
            gap = np.random.normal(0, 0.01)  # 跳空
            open_price = current_price * (1 + gap)
            
            # 计算收盘价
            close_price = open_price * (1 + daily_change + trend_factor)
            
            # 计算最高价和最低价
            intraday_volatility = abs(np.random.normal(0, 0.015))
            high_price = max(open_price, close_price) * (1 + intraday_volatility)
            low_price = min(open_price, close_price) * (1 - intraday_volatility)
            
            # 生成成交量（基于价格变化）
            volume_base = np.random.uniform(1000000, 5000000)
            volume_multiplier = 1 + abs(daily_change) * 2  # 价格变化大时成交量增加
            volume = int(volume_base * volume_multiplier)
            
            # 计算成交额
            amount = volume * (high_price + low_price + open_price + close_price) / 4
            
            # 计算换手率
            turnover_rate = np.random.uniform(0.5, 8.0)
            
            price_data = {
                "stock_code": stock_code,
                "date": current_date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume,
                "amount": round(amount, 2),
                "turnover_rate": round(turnover_rate, 2),
                "created_at": datetime.now().isoformat()
            }
            
            prices.append(price_data)
            
            # 更新当前价格
            current_price = close_price
            current_date += timedelta(days=1)
            
        return prices
        
    def _generate_pe_ratio(self, industry: str) -> float:
        """根据行业生成PE比率"""
        industry_pe_ranges = {
            "银行": (4, 8),
            "白酒": (20, 40),
            "房地产开发": (6, 12),
            "安防设备": (15, 30),
            "证券": (10, 20),
            "显示器件": (12, 25)
        }
        
        pe_range = industry_pe_ranges.get(industry, (10, 25))
        return round(np.random.uniform(*pe_range), 2)
        
    def _generate_pb_ratio(self, industry: str) -> float:
        """根据行业生成PB比率"""
        industry_pb_ranges = {
            "银行": (0.5, 1.2),
            "白酒": (3, 8),
            "房地产开发": (0.8, 2.0),
            "安防设备": (2, 5),
            "证券": (1, 3),
            "显示器件": (1.5, 4)
        }
        
        pb_range = industry_pb_ranges.get(industry, (1, 4))
        return round(np.random.uniform(*pb_range), 2)
        
    def _generate_market_cap(self, industry: str) -> float:
        """根据行业生成市值"""
        industry_cap_ranges = {
            "银行": (1000, 5000),      # 亿元
            "白酒": (2000, 8000),
            "房地产开发": (500, 3000),
            "安防设备": (300, 1500),
            "证券": (800, 3000),
            "显示器件": (200, 1000)
        }
        
        cap_range = industry_cap_ranges.get(industry, (500, 2000))
        return round(np.random.uniform(*cap_range) * 1e8, 2)  # 转换为元
        
    def _generate_revenue(self, industry: str) -> float:
        """根据行业生成营收"""
        industry_revenue_ranges = {
            "银行": (500, 2000),       # 亿元
            "白酒": (300, 1200),
            "房地产开发": (800, 3000),
            "安防设备": (200, 800),
            "证券": (100, 500),
            "显示器件": (300, 1500)
        }
        
        revenue_range = industry_revenue_ranges.get(industry, (200, 1000))
        return round(np.random.uniform(*revenue_range) * 1e8, 2)  # 转换为元
        
    def _generate_net_profit(self, industry: str) -> float:
        """根据行业生成净利润"""
        industry_profit_margins = {
            "银行": (0.15, 0.30),
            "白酒": (0.20, 0.40),
            "房地产开发": (0.08, 0.15),
            "安防设备": (0.10, 0.20),
            "证券": (0.15, 0.35),
            "显示器件": (0.05, 0.12)
        }
        
        margin_range = industry_profit_margins.get(industry, (0.08, 0.20))
        margin = np.random.uniform(*margin_range)
        revenue = self._generate_revenue(industry)
        
        return round(revenue * margin, 2)
        
    def _generate_realistic_price(self, industry: str) -> float:
        """生成符合行业特征的价格"""
        industry_price_ranges = {
            "银行": (8, 25),
            "白酒": (100, 300),
            "房地产开发": (5, 30),
            "安防设备": (20, 60),
            "证券": (10, 40),
            "显示器件": (3, 15)
        }
        
        price_range = industry_price_ranges.get(industry, (10, 50))
        return np.random.uniform(*price_range)
        
    def _generate_recommendation_reason(self, signal_type: str, industry: str) -> str:
        """生成推荐理由"""
        buy_reasons = [
            "技术指标显示突破关键阻力位，成交量放大确认",
            "MACD金叉信号明确，短期均线上穿长期均线",
            "RSI从超卖区域反弹，显示买入时机",
            "布林带下轨支撑有效，价格开始回升",
            "基本面改善，业绩预期向好",
            "行业景气度提升，政策利好频出",
            "机构资金流入明显，主力建仓迹象",
            "技术形态良好，多头排列形成"
        ]
        
        sell_reasons = [
            "技术指标显示顶部信号，建议获利了结",
            "MACD死叉确认，短期调整压力加大",
            "RSI进入超买区域，回调风险增加",
            "布林带上轨压力明显，上涨动能不足",
            "基本面恶化，业绩不及预期",
            "行业面临政策压力，前景不明",
            "资金流出明显，主力减仓迹象",
            "技术形态破位，空头排列形成"
        ]
        
        reasons = buy_reasons if signal_type == 'buy' else sell_reasons
        return np.random.choice(reasons)
        
    # 技术指标计算方法
    def _calculate_ma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """计算移动平均线"""
        return pd.Series(prices).rolling(window=period).mean().values
        
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """计算RSI"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean()
        avg_losses = pd.Series(losses).rolling(window=period).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return np.concatenate([[np.nan], rsi.values])
        
    def _calculate_macd(self, prices: np.ndarray, fast=12, slow=26, signal=9):
        """计算MACD"""
        exp1 = pd.Series(prices).ewm(span=fast).mean()
        exp2 = pd.Series(prices).ewm(span=slow).mean()
        
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal).mean()
        macd_hist = macd - macd_signal
        
        return macd.values, macd_signal.values, macd_hist.values
        
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: int = 2):
        """计算布林带"""
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band.values, sma.values, lower_band.values
        
    def _calculate_kdj(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 9):
        """计算KDJ"""
        lowest_lows = pd.Series(lows).rolling(window=period).min()
        highest_highs = pd.Series(highs).rolling(window=period).max()
        
        rsv = (closes - lowest_lows) / (highest_highs - lowest_lows) * 100
        
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d
        
        return k.values, d.values, j.values
        
    def generate_all_test_data(self, days: int = 365):
        """生成所有测试数据"""
        print("🚀 开始生成完整测试数据集...")
        print(f"📅 数据时间范围: {days} 天")
        print(f"📊 股票数量: {len(self.real_stocks)}")
        print(f"📁 数据目录: {self.data_dir}")
        
        # 1. 生成股票基础信息
        stocks_df = self.generate_stock_basic_info()
        
        # 2. 生成价格数据
        prices_df = self.generate_stock_prices(days)
        
        # 3. 生成基本面数据
        fundamentals_df = self.generate_stock_fundamentals()
        
        # 4. 生成技术指标
        indicators_df = self.generate_technical_indicators(prices_df)
        
        # 5. 生成示例推荐
        recommendations_df = self.generate_sample_recommendations()
        
        # 6. 生成数据摘要
        self._generate_data_summary({
            "stocks": len(stocks_df),
            "prices": len(prices_df),
            "fundamentals": len(fundamentals_df),
            "indicators": len(indicators_df),
            "recommendations": len(recommendations_df)
        })
        
        print("\n🎉 测试数据生成完成！")
        print("\n📊 数据统计:")
        print(f"   📈 股票数量: {len(stocks_df)}")
        print(f"   📊 价格记录: {len(prices_df):,}")
        print(f"   📋 基本面记录: {len(fundamentals_df):,}")
        print(f"   📈 技术指标记录: {len(indicators_df):,}")
        print(f"   💡 推荐记录: {len(recommendations_df)}")
        
        return {
            "stocks": stocks_df,
            "prices": prices_df,
            "fundamentals": fundamentals_df,
            "indicators": indicators_df,
            "recommendations": recommendations_df
        }
        
    def _generate_data_summary(self, stats: Dict[str, int]):
        """生成数据摘要文件"""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "data_directory": self.data_dir,
            "statistics": stats,
            "files": {
                "stocks": "stocks.csv",
                "prices": "stock_prices.csv",
                "fundamentals": "stock_fundamentals.csv",
                "indicators": "technical_indicators.csv",
                "recommendations": "recommendations.csv"
            },
            "stock_list": self.real_stocks
        }
        
        summary_file = os.path.join(self.data_dir, "data_summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 数据摘要已保存: {summary_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成股票推荐系统测试数据")
    parser.add_argument("--days", type=int, default=365, help="生成多少天的历史数据")
    parser.add_argument("--data-dir", default="data/csv", help="数据保存目录")
    parser.add_argument("--stocks-only", action="store_true", help="只生成股票基础信息")
    parser.add_argument("--prices-only", action="store_true", help="只生成价格数据")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(data_dir=args.data_dir)
    
    if args.stocks_only:
        generator.generate_stock_basic_info()
    elif args.prices_only:
        stocks_df = generator.generate_stock_basic_info()
        generator.generate_stock_prices(args.days)
    else:
        generator.generate_all_test_data(args.days)

if __name__ == "__main__":
    main()