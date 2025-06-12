#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
功能：调度上述模块，输出推荐结果与卖出建议
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import schedule
import time

from data_fetcher import DataFetcher
from feature_extractor import FeatureExtractor
from scoring_engine import ScoringEngine
from sell_decision import SellDecision

# 确保结果目录存在
os.makedirs('result', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('result/stock_recommendation.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True  # 强制重新配置日志
)
logger = logging.getLogger(__name__)

class StockRecommendationSystem:
    """股票推荐系统主类"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.feature_extractor = FeatureExtractor()
        self.scoring_engine = ScoringEngine()
        self.sell_decision = SellDecision()
        
        # 系统配置
        self.config = {
            'max_stocks_to_analyze': 500,  # 最大分析股票数量
            'top_recommendations': 20,     # 推荐股票数量
            'min_price': 3.0,             # 最低价格过滤
            'max_price': 200.0,           # 最高价格过滤
            'exclude_st': True,           # 排除ST股票
            'exclude_new_stocks': True,   # 排除新股（上市不足30天）
        }
    
    def filter_stock_universe(self, stock_list: List[Dict]) -> List[str]:
        """筛选股票池"""
        logger.info("开始筛选股票池...")
        
        filtered_codes = []
        
        for stock in stock_list:
            stock_code = stock.get('code', '')
            stock_name = stock.get('name', '')
            
            # 基本过滤条件
            if not stock_code or not stock_name:
                continue
            
            # 排除ST股票
            if self.config['exclude_st'] and ('ST' in stock_name or '*ST' in stock_name):
                continue
            
            # 排除科创板和创业板（可选）
            if stock_code.startswith('688') or stock_code.startswith('300'):
                continue
            
            filtered_codes.append(stock_code)
        
        # 限制分析数量
        if len(filtered_codes) > self.config['max_stocks_to_analyze']:
            filtered_codes = filtered_codes[:self.config['max_stocks_to_analyze']]
        
        logger.info(f"筛选后股票池包含{len(filtered_codes)}只股票")
        return filtered_codes
    
    def generate_buy_recommendations(self) -> Dict:
        """生成买入推荐"""
        logger.info("="*50)
        logger.info("开始生成买入推荐")
        logger.info("="*50)
        
        try:
            # 1. 获取股票列表
            logger.info("步骤1: 获取股票列表")
            try:
                stock_list = self.data_fetcher.get_stock_list()
                if stock_list.empty:
                    raise Exception("获取到的股票列表为空")
            except Exception as e:
                raise Exception(f"获取股票列表失败: {e}")
            
            # 转换为字典列表
            stock_list_dict = stock_list.to_dict('records')
            
            # 2. 筛选股票池
            logger.info("步骤2: 筛选股票池")
            filtered_codes = self.filter_stock_universe(stock_list_dict)
            
            if not filtered_codes:
                raise Exception("筛选后股票池为空")
            
            # 3. 获取数据
            logger.info("步骤3: 获取股票数据")
            try:
                all_stock_data = self.data_fetcher.get_all_data(filtered_codes)
                
                if not all_stock_data:
                    raise Exception("无法获取任何股票数据")
                    
                logger.info(f"成功获取{len(all_stock_data)}只股票的数据")
                
            except Exception as e:
                raise Exception(f"获取股票数据失败: {e}")
            
            # 添加股票名称信息
            stock_name_map = {stock['code']: stock['name'] for stock in stock_list_dict}
            for code, data in all_stock_data.items():
                if 'realtime' in data:
                    data['realtime']['stock_name'] = stock_name_map.get(code, '')
            
            # 4. 提取特征
            logger.info("步骤4: 提取特征")
            all_features = self.feature_extractor.batch_extract_features(all_stock_data)
            
            if not all_features:
                raise Exception("特征提取失败")
            
            # 添加股票名称到特征中
            for code, features in all_features.items():
                features['stock_name'] = stock_name_map.get(code, '')
            
            # 5. 计算得分
            logger.info("步骤5: 计算股票得分")
            scored_stocks = self.scoring_engine.score_stocks(all_features)
            
            # 6. 获取推荐
            logger.info("步骤6: 生成推荐列表")
            top_stocks = self.scoring_engine.get_top_recommendations(
                scored_stocks, self.config['top_recommendations']
            )
            
            # 7. 格式化结果
            logger.info("步骤7: 格式化推荐结果")
            formatted_results = self.scoring_engine.format_recommendation_result(top_stocks)
            
            # 8. 生成最终结果
            result = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'total_analyzed': len(all_features),
                'total_recommended': len(formatted_results),
                'recommendations': formatted_results,
                'system_info': {
                    'version': '1.0',
                    'config': self.config
                }
            }
            
            logger.info(f"买入推荐生成完成，共推荐{len(formatted_results)}只股票")
            return result
            
        except Exception as e:
            logger.error(f"生成买入推荐失败: {e}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'error': str(e),
                'recommendations': []
            }
    
    def generate_sell_recommendations(self) -> Dict:
        """生成卖出建议"""
        logger.info("="*50)
        logger.info("开始生成卖出建议")
        logger.info("="*50)
        
        try:
            # 执行卖出分析
            sell_result = self.sell_decision.execute_sell_analysis()
            
            logger.info(f"卖出建议生成完成")
            return sell_result
            
        except Exception as e:
            logger.error(f"生成卖出建议失败: {e}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'error': str(e),
                'decisions': []
            }
    
    def save_results(self, buy_result: Dict, sell_result: Dict) -> None:
        """保存结果到文件"""
        today = datetime.now().strftime('%Y%m%d')
        
        # 保存买入推荐
        if buy_result.get('recommendations'):
            buy_file = f"result/buy_{today}.json"
            try:
                with open(buy_file, 'w', encoding='utf-8') as f:
                    json.dump(buy_result, f, ensure_ascii=False, indent=2)
                logger.info(f"买入推荐已保存到: {buy_file}")
            except Exception as e:
                logger.error(f"保存买入推荐失败: {e}")
        
        # 保存卖出建议
        if sell_result.get('decisions'):
            sell_file = f"result/sell_{today}.json"
            try:
                with open(sell_file, 'w', encoding='utf-8') as f:
                    json.dump(sell_result, f, ensure_ascii=False, indent=2)
                logger.info(f"卖出建议已保存到: {sell_file}")
            except Exception as e:
                logger.error(f"保存卖出建议失败: {e}")
    
    def print_summary(self, buy_result: Dict, sell_result: Dict) -> None:
        """打印结果摘要"""
        print("\n" + "="*60)
        print(f"股票推荐系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 买入推荐摘要
        print("\n【买入推荐】")
        if buy_result.get('recommendations'):
            print(f"共推荐 {len(buy_result['recommendations'])} 只股票:")
            for i, stock in enumerate(buy_result['recommendations'][:5], 1):
                print(f"{i:2d}. {stock['stock_name']}({stock['stock_code']}) - "
                      f"价格: {stock['current_price']:.2f} - 得分: {stock['total_score']:.2f}")
                print(f"     推荐理由: {stock['recommendation_reason']}")
            
            if len(buy_result['recommendations']) > 5:
                print(f"     ... 还有 {len(buy_result['recommendations']) - 5} 只股票")
        else:
            print("今日无推荐股票")
        
        # 卖出建议摘要
        print("\n【卖出建议】")
        if sell_result.get('decisions'):
            summary = sell_result.get('summary', {})
            print(f"共分析 {summary.get('total_stocks', 0)} 只持仓股票:")
            print(f"  建议卖出: {summary.get('sell_count', 0)} 只")
            print(f"  建议减仓: {summary.get('reduce_count', 0)} 只")
            print(f"  继续持有: {summary.get('hold_count', 0)} 只")
            print(f"  平均收益率: {summary.get('avg_return_rate', 0):.2f}%")
            
            # 显示需要操作的股票
            action_stocks = [d for d in sell_result['decisions'] 
                           if d['action'] in ['SELL', 'REDUCE']]
            if action_stocks:
                print("\n需要操作的股票:")
                for stock in action_stocks[:5]:
                    action_text = "卖出" if stock['action'] == 'SELL' else f"减仓{stock['sell_ratio']*100:.0f}%"
                    print(f"  {stock['stock_name']}({stock['stock_code']}) - {action_text}")
                    print(f"    收益率: {stock['return_rate']:.2f}% - {stock['reason']}")
        else:
            print("无持仓股票需要分析")
        
        print("\n" + "="*60)
    
    def run_daily_analysis(self) -> None:
        """执行每日分析"""
        logger.info("开始执行每日股票分析")
        start_time = time.time()
        
        try:
            # 生成买入推荐（14:45执行）
            buy_result = self.generate_buy_recommendations()
            
            # 生成卖出建议（9:45执行）
            sell_result = self.generate_sell_recommendations()
            
            # 保存结果
            self.save_results(buy_result, sell_result)
            
            # 打印摘要
            self.print_summary(buy_result, sell_result)
            
            end_time = time.time()
            logger.info(f"每日分析完成，耗时: {end_time - start_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"每日分析失败: {e}")
    
    def run_buy_analysis_only(self) -> None:
        """仅执行买入分析（14:45）"""
        logger.info("执行买入分析")
        
        buy_result = self.generate_buy_recommendations()
        
        # 保存买入推荐
        today = datetime.now().strftime('%Y%m%d')
        buy_file = f"result/buy_{today}.json"
        
        try:
            with open(buy_file, 'w', encoding='utf-8') as f:
                json.dump(buy_result, f, ensure_ascii=False, indent=2)
            logger.info(f"买入推荐已保存到: {buy_file}")
        except Exception as e:
            logger.error(f"保存买入推荐失败: {e}")
        
        # 打印买入推荐
        if buy_result.get('recommendations'):
            print(f"\n今日买入推荐 ({len(buy_result['recommendations'])}只):")
            for i, stock in enumerate(buy_result['recommendations'], 1):
                print(f"{i:2d}. {stock['stock_name']}({stock['stock_code']}) - "
                      f"价格: {stock['current_price']:.2f} - 得分: {stock['total_score']:.2f}")
    
    def run_sell_analysis_only(self) -> None:
        """仅执行卖出分析（9:45）"""
        logger.info("执行卖出分析")
        
        sell_result = self.generate_sell_recommendations()
        
        # 保存卖出建议
        today = datetime.now().strftime('%Y%m%d')
        sell_file = f"result/sell_{today}.json"
        
        try:
            with open(sell_file, 'w', encoding='utf-8') as f:
                json.dump(sell_result, f, ensure_ascii=False, indent=2)
            logger.info(f"卖出建议已保存到: {sell_file}")
        except Exception as e:
            logger.error(f"保存卖出建议失败: {e}")
        
        # 打印卖出建议
        if sell_result.get('decisions'):
            summary = sell_result.get('summary', {})
            print(f"\n今日卖出建议 (分析{summary.get('total_stocks', 0)}只):")
            print(f"建议卖出: {summary.get('sell_count', 0)}只, "
                  f"建议减仓: {summary.get('reduce_count', 0)}只, "
                  f"继续持有: {summary.get('hold_count', 0)}只")
    
    def setup_scheduler(self) -> None:
        """设置定时任务"""
        # 每个交易日14:45执行买入分析
        schedule.every().monday.at("14:45").do(self.run_buy_analysis_only)
        schedule.every().tuesday.at("14:45").do(self.run_buy_analysis_only)
        schedule.every().wednesday.at("14:45").do(self.run_buy_analysis_only)
        schedule.every().thursday.at("14:45").do(self.run_buy_analysis_only)
        schedule.every().friday.at("14:45").do(self.run_buy_analysis_only)
        
        # 每个交易日9:45执行卖出分析
        schedule.every().monday.at("09:45").do(self.run_sell_analysis_only)
        schedule.every().tuesday.at("09:45").do(self.run_sell_analysis_only)
        schedule.every().wednesday.at("09:45").do(self.run_sell_analysis_only)
        schedule.every().thursday.at("09:45").do(self.run_sell_analysis_only)
        schedule.every().friday.at("09:45").do(self.run_sell_analysis_only)
        
        logger.info("定时任务设置完成")
    
    def run_scheduler(self) -> None:
        """运行定时任务"""
        self.setup_scheduler()
        
        logger.info("股票推荐系统启动，等待定时执行...")
        logger.info("买入分析时间: 每个交易日 14:45")
        logger.info("卖出分析时间: 每个交易日 09:45")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

def main():
    """主函数"""
    import sys
    
    system = StockRecommendationSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'buy':
            system.run_buy_analysis_only()
        elif command == 'sell':
            system.run_sell_analysis_only()
        elif command == 'both':
            system.run_daily_analysis()
        elif command == 'schedule':
            system.run_scheduler()
        else:
            print("使用方法:")
            print("  python main.py buy      # 执行买入分析")
            print("  python main.py sell     # 执行卖出分析")
            print("  python main.py both     # 执行完整分析")
            print("  python main.py schedule # 启动定时任务")
    else:
        # 默认执行完整分析
        system.run_daily_analysis()

if __name__ == "__main__":
    main()