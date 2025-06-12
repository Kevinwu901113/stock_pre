#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日卖出信号检查脚本
用于每日9:45自动检查前一日推荐股票的卖出信号
可以通过定时任务(cron)自动执行
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
import logging
from enhanced_sell_signal import EnhancedSellSignal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sell_signal_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailySellSignalChecker:
    """每日卖出信号检查器"""
    
    def __init__(self, config_file=None, output_dir="results"):
        self.config_file = config_file or "sell_signal_config.json"
        self.output_dir = output_dir
        self.sell_analyzer = EnhancedSellSignal(self.config_file)
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def check_trading_time(self):
        """检查是否在交易时间内"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # 检查是否为交易日（简单检查，实际应该检查节假日）
        if now.weekday() >= 5:  # 周六、周日
            logger.warning(f"今日为周末，非交易日")
            return False
        
        # 检查是否在交易时间内
        if current_time < '09:30' or current_time > '15:00':
            logger.warning(f"当前时间 {current_time} 不在交易时间内")
            return False
        
        return True
    
    def send_alert(self, urgent_decisions, medium_decisions):
        """发送告警通知"""
        try:
            # 这里可以集成实际的通知系统
            # 例如：邮件、短信、微信、钉钉等
            
            if urgent_decisions:
                logger.warning(f"🚨 紧急卖出信号: {len(urgent_decisions)}只股票需要立即处理")
                for decision in urgent_decisions:
                    logger.warning(
                        f"  {decision['stock_name']}({decision['stock_code']}): "
                        f"{decision['action']} - {decision['reason']}"
                    )
            
            if medium_decisions:
                logger.info(f"⚠️ 中等紧急度信号: {len(medium_decisions)}只股票需要关注")
                for decision in medium_decisions:
                    logger.info(
                        f"  {decision['stock_name']}({decision['stock_code']}): "
                        f"{decision['action']} - {decision['reason']}"
                    )
            
            # TODO: 实际项目中可以在这里添加:
            # - 发送邮件通知
            # - 发送短信告警
            # - 推送到交易系统
            # - 记录到数据库
            
        except Exception as e:
            logger.error(f"发送告警失败: {e}")
    
    def generate_trading_report(self, results):
        """生成交易报告"""
        try:
            summary = results['summary']
            decisions = results['decisions']
            
            # 生成简化的交易报告
            report = {
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "report_time": datetime.now().strftime("%H:%M:%S"),
                "total_positions": summary['total_stocks'],
                "actions_required": sum(1 for d in decisions if d['action'] != '继续持有'),
                "urgent_actions": sum(1 for d in decisions if d.get('urgency') == 'HIGH'),
                "expected_profit_loss": {
                    "total_return": summary['return_stats']['avg_return'],
                    "profit_positions": summary['return_stats']['positive_count'],
                    "loss_positions": summary['return_stats']['negative_count']
                },
                "action_summary": summary['action_distribution'],
                "signal_summary": summary['signal_distribution'],
                "recommendations": [
                    {
                        "stock": f"{d['stock_name']}({d['stock_code']})",
                        "action": d['action'],
                        "reason": d['reason'],
                        "urgency": d.get('urgency', 'LOW'),
                        "return": f"{d.get('change_percent', 0):+.2f}%"
                    }
                    for d in decisions if d['action'] != '继续持有'
                ]
            }
            
            # 保存交易报告
            report_filename = f"{self.output_dir}/trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"交易报告已生成: {report_filename}")
            return report_filename
            
        except Exception as e:
            logger.error(f"生成交易报告失败: {e}")
            return None
    
    def run_daily_check(self, force=False):
        """执行每日检查"""
        logger.info("开始执行每日卖出信号检查")
        
        # 检查交易时间（除非强制执行）
        if not force and not self.check_trading_time():
            return None
        
        try:
            # 执行卖出信号分析
            results = self.sell_analyzer.analyze_sell_signals()
            
            if not results or results['summary']['total_stocks'] == 0:
                logger.info("未找到需要分析的股票")
                return None
            
            # 保存详细结果
            filename = self.sell_analyzer.save_results(results, self.output_dir)
            
            # 分析决策并发送告警
            decisions = results['decisions']
            urgent_decisions = [d for d in decisions if d.get('urgency') == 'HIGH']
            medium_decisions = [d for d in decisions if d.get('urgency') == 'MEDIUM']
            
            # 发送告警
            self.send_alert(urgent_decisions, medium_decisions)
            
            # 生成交易报告
            report_filename = self.generate_trading_report(results)
            
            # 记录执行结果
            summary = results['summary']
            logger.info(
                f"卖出信号检查完成: 分析{summary['total_stocks']}只股票, "
                f"紧急操作{len(urgent_decisions)}只, 中等紧急{len(medium_decisions)}只"
            )
            
            return {
                'results_file': filename,
                'report_file': report_filename,
                'urgent_count': len(urgent_decisions),
                'medium_count': len(medium_decisions),
                'total_count': summary['total_stocks']
            }
            
        except Exception as e:
            logger.error(f"每日检查执行失败: {e}")
            return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='每日卖出信号检查')
    parser.add_argument('--config', '-c', help='配置文件路径', default='sell_signal_config.json')
    parser.add_argument('--output', '-o', help='输出目录', default='results')
    parser.add_argument('--force', '-f', action='store_true', help='强制执行（忽略时间检查）')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--date', '-d', help='指定分析日期 (YYYYMMDD)')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # 初始化检查器
    checker = DailySellSignalChecker(args.config, args.output)
    
    # 如果指定了日期，需要修改分析器的日期参数
    if args.date:
        # 这里可以扩展为支持指定日期的分析
        logger.info(f"指定分析日期: {args.date}")
    
    # 执行检查
    result = checker.run_daily_check(args.force)
    
    if result:
        print(f"✅ 检查完成")
        print(f"📄 详细结果: {result['results_file']}")
        print(f"📊 交易报告: {result['report_file']}")
        print(f"🚨 紧急操作: {result['urgent_count']}只")
        print(f"⚠️ 中等紧急: {result['medium_count']}只")
        print(f"📈 总计分析: {result['total_count']}只")
        
        # 设置退出码
        if result['urgent_count'] > 0:
            sys.exit(2)  # 有紧急操作
        elif result['medium_count'] > 0:
            sys.exit(1)  # 有中等紧急操作
        else:
            sys.exit(0)  # 正常
    else:
        print("❌ 检查失败或无数据")
        sys.exit(3)

if __name__ == "__main__":
    main()