# -*- coding: utf-8 -*-
"""
结果输出模块
功能：负责推荐结果的格式化输出、文件管理和备份
"""

import os
import json
import yaml
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ResultWriter:
    """结果输出类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化结果输出器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.output_config = self.config.get('output', {})
        self.result_dir = self.output_config.get('result_dir', 'result')
        self.file_format = self.output_config.get('file_format', 'json')
        self.include_details = self.output_config.get('include_details', True)
        self.backup_days = self.output_config.get('backup_days', 30)
        
        # 确保结果目录存在
        self._ensure_result_dir()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _ensure_result_dir(self):
        """确保结果目录存在"""
        Path(self.result_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"结果目录已准备: {self.result_dir}")
    
    def write_buy_recommendations(self, recommendations: List[Dict], 
                                date: str = None) -> str:
        """输出买入推荐结果
        
        Args:
            recommendations: 推荐结果列表
            date: 日期字符串，格式YYYYMMDD
            
        Returns:
            输出文件路径
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        filename = f"buy_{date}.{self.file_format}"
        filepath = os.path.join(self.result_dir, filename)
        
        # 格式化推荐结果
        formatted_data = self._format_buy_recommendations(recommendations, date)
        
        # 写入文件
        self._write_file(filepath, formatted_data)
        
        logger.info(f"买入推荐结果已输出到: {filepath}")
        return filepath
    
    def write_sell_decisions(self, sell_decisions: List[Dict], 
                           date: str = None) -> str:
        """输出卖出决策结果
        
        Args:
            sell_decisions: 卖出决策列表
            date: 日期字符串，格式YYYYMMDD
            
        Returns:
            输出文件路径
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        filename = f"sell_{date}.{self.file_format}"
        filepath = os.path.join(self.result_dir, filename)
        
        # 格式化卖出决策
        formatted_data = self._format_sell_decisions(sell_decisions, date)
        
        # 写入文件
        self._write_file(filepath, formatted_data)
        
        logger.info(f"卖出决策结果已输出到: {filepath}")
        return filepath
    
    def _format_buy_recommendations(self, recommendations: List[Dict], 
                                  date: str) -> Dict:
        """格式化买入推荐数据"""
        formatted_data = {
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "total_count": len(recommendations),
            "recommendations": []
        }
        
        for i, rec in enumerate(recommendations, 1):
            formatted_rec = {
                "rank": i,
                "stock_code": rec.get('stock_code', ''),
                "stock_name": rec.get('stock_name', ''),
                "current_price": rec.get('current_price', 0),
                "total_score": round(rec.get('total_score', 0), 4),
                "change_pct": rec.get('change_pct', 0),
                "volume_ratio": rec.get('volume_ratio', 0),
                "recommendation_reason": rec.get('recommendation_reason', '')
            }
            
            # 如果包含详细信息
            if self.include_details:
                formatted_rec.update({
                    "factor_scores": rec.get('factor_scores', {}),
                    "technical_indicators": rec.get('technical_indicators', {}),
                    "risk_metrics": rec.get('risk_metrics', {})
                })
            
            formatted_data["recommendations"].append(formatted_rec)
        
        return formatted_data
    
    def _format_sell_decisions(self, sell_decisions: List[Dict], 
                             date: str) -> Dict:
        """格式化卖出决策数据"""
        formatted_data = {
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "total_count": len(sell_decisions),
            "sell_decisions": []
        }
        
        for decision in sell_decisions:
            formatted_decision = {
                "stock_code": decision.get('stock_code', ''),
                "stock_name": decision.get('stock_name', ''),
                "buy_price": decision.get('buy_price', 0),
                "current_price": decision.get('current_price', 0),
                "return_rate": round(decision.get('return_rate', 0), 2),
                "should_sell": decision.get('should_sell', False),
                "sell_reason": decision.get('sell_reason', ''),
                "hold_days": decision.get('hold_days', 0)
            }
            
            # 如果包含详细信息
            if self.include_details:
                formatted_decision.update({
                    "technical_signals": decision.get('technical_signals', {}),
                    "risk_signals": decision.get('risk_signals', {})
                })
            
            formatted_data["sell_decisions"].append(formatted_decision)
        
        return formatted_data
    
    def _write_file(self, filepath: str, data: Dict):
        """写入文件"""
        try:
            if self.file_format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif self.file_format.lower() == 'yaml':
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            else:
                raise ValueError(f"不支持的文件格式: {self.file_format}")
        except Exception as e:
            logger.error(f"写入文件失败 {filepath}: {e}")
            raise
    
    def load_previous_recommendations(self, date: str = None) -> List[Dict]:
        """加载前一天的推荐结果
        
        Args:
            date: 日期字符串，格式YYYYMMDD，如果为None则自动计算前一个交易日
            
        Returns:
            推荐结果列表
        """
        if date is None:
            # 计算前一个交易日
            today = datetime.now()
            if today.weekday() == 0:  # 周一
                previous_date = (today - timedelta(days=3)).strftime('%Y%m%d')
            else:
                previous_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        else:
            previous_date = date
        
        filename = f"buy_{previous_date}.{self.file_format}"
        filepath = os.path.join(self.result_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"未找到前一天的推荐文件: {filepath}")
            return []
        
        try:
            if self.file_format.lower() == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif self.file_format.lower() == 'yaml':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的文件格式: {self.file_format}")
            
            recommendations = data.get('recommendations', [])
            logger.info(f"加载了{len(recommendations)}只前日推荐股票")
            return recommendations
            
        except Exception as e:
            logger.error(f"加载推荐文件失败: {e}")
            return []
    
    def cleanup_old_files(self):
        """清理过期的结果文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_days)
            cutoff_str = cutoff_date.strftime('%Y%m%d')
            
            result_path = Path(self.result_dir)
            deleted_count = 0
            
            for file_path in result_path.glob(f"*.{self.file_format}"):
                # 提取文件名中的日期
                filename = file_path.stem
                if '_' in filename:
                    date_part = filename.split('_')[-1]
                    if len(date_part) == 8 and date_part.isdigit():
                        if date_part < cutoff_str:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"删除过期文件: {file_path}")
            
            if deleted_count > 0:
                logger.info(f"清理了{deleted_count}个过期结果文件")
                
        except Exception as e:
            logger.error(f"清理过期文件失败: {e}")
    
    def export_to_excel(self, data: Dict, filepath: str):
        """导出数据到Excel文件
        
        Args:
            data: 要导出的数据
            filepath: Excel文件路径
        """
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                if 'recommendations' in data:
                    # 买入推荐数据
                    df = pd.DataFrame(data['recommendations'])
                    df.to_excel(writer, sheet_name='买入推荐', index=False)
                
                if 'sell_decisions' in data:
                    # 卖出决策数据
                    df = pd.DataFrame(data['sell_decisions'])
                    df.to_excel(writer, sheet_name='卖出决策', index=False)
            
            logger.info(f"数据已导出到Excel: {filepath}")
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            raise
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """获取系统性能摘要
        
        Args:
            days: 统计天数
            
        Returns:
            性能摘要字典
        """
        try:
            result_path = Path(self.result_dir)
            buy_files = list(result_path.glob(f"buy_*.{self.file_format}"))
            sell_files = list(result_path.glob(f"sell_*.{self.file_format}"))
            
            # 统计最近N天的文件
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime('%Y%m%d')
            
            recent_buy_files = []
            recent_sell_files = []
            
            for file_path in buy_files:
                date_part = file_path.stem.split('_')[-1]
                if len(date_part) == 8 and date_part.isdigit() and date_part >= cutoff_str:
                    recent_buy_files.append(file_path)
            
            for file_path in sell_files:
                date_part = file_path.stem.split('_')[-1]
                if len(date_part) == 8 and date_part.isdigit() and date_part >= cutoff_str:
                    recent_sell_files.append(file_path)
            
            summary = {
                "period_days": days,
                "total_buy_recommendations": len(recent_buy_files),
                "total_sell_decisions": len(recent_sell_files),
                "latest_buy_date": max([f.stem.split('_')[-1] for f in recent_buy_files]) if recent_buy_files else None,
                "latest_sell_date": max([f.stem.split('_')[-1] for f in recent_sell_files]) if recent_sell_files else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取性能摘要失败: {e}")
            return {}