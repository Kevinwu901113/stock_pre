#!/usr/bin/env python3
"""
AI模型下载脚本

用于下载和管理AI模型文件。
"""

import os
import sys
import requests
import hashlib
from pathlib import Path
from typing import Dict, List
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


class ModelDownloader:
    """AI模型下载器"""
    
    def __init__(self):
        self.models_dir = project_root / "ai" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型配置
        self.model_configs = {
            # 情感分析模型
            'sentiment_bert': {
                'url': 'https://huggingface.co/bert-base-chinese/resolve/main/pytorch_model.bin',
                'path': 'sentiment/bert_sentiment.bin',
                'size': '400MB',
                'description': 'BERT中文情感分析模型',
                'required': False
            },
            
            # 价格预测模型
            'lstm_price': {
                'url': 'https://example.com/models/lstm_price.h5',
                'path': 'prediction/lstm_price.h5',
                'size': '50MB',
                'description': 'LSTM股价预测模型',
                'required': False
            },
            
            # 推荐系统模型
            'collaborative_filter': {
                'url': 'https://example.com/models/collaborative_filter.pkl',
                'path': 'recommendation/collaborative_filter.pkl',
                'size': '20MB',
                'description': '协同过滤推荐模型',
                'required': False
            },
            
            # 预训练词向量
            'financial_word2vec': {
                'url': 'https://example.com/models/financial_word2vec.bin',
                'path': 'pretrained/financial_word2vec.bin',
                'size': '200MB',
                'description': '金融领域词向量模型',
                'required': False
            }
        }
    
    def list_models(self) -> None:
        """列出所有可用的模型"""
        print("\n可用的AI模型:")
        print("=" * 60)
        
        for name, config in self.model_configs.items():
            status = "已安装" if self.is_model_installed(name) else "未安装"
            required = "必需" if config['required'] else "可选"
            
            print(f"名称: {name}")
            print(f"描述: {config['description']}")
            print(f"大小: {config['size']}")
            print(f"状态: {status}")
            print(f"类型: {required}")
            print("-" * 40)
    
    def is_model_installed(self, model_name: str) -> bool:
        """检查模型是否已安装"""
        if model_name not in self.model_configs:
            return False
        
        model_path = self.models_dir / self.model_configs[model_name]['path']
        return model_path.exists()
    
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """下载指定模型"""
        if model_name not in self.model_configs:
            logger.error(f"未知的模型: {model_name}")
            return False
        
        config = self.model_configs[model_name]
        model_path = self.models_dir / config['path']
        
        # 检查是否已存在
        if model_path.exists() and not force:
            logger.info(f"模型 {model_name} 已存在，跳过下载")
            return True
        
        # 创建目录
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"开始下载模型: {model_name}")
            logger.info(f"URL: {config['url']}")
            logger.info(f"大小: {config['size']}")
            
            # 下载文件
            response = requests.get(config['url'], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end='', flush=True)
            
            print()  # 换行
            logger.success(f"模型 {model_name} 下载完成")
            return True
            
        except Exception as e:
            logger.error(f"下载模型 {model_name} 失败: {e}")
            # 删除不完整的文件
            if model_path.exists():
                model_path.unlink()
            return False
    
    def download_all_models(self, required_only: bool = False) -> None:
        """下载所有模型"""
        models_to_download = []
        
        for name, config in self.model_configs.items():
            if required_only and not config['required']:
                continue
            if not self.is_model_installed(name):
                models_to_download.append(name)
        
        if not models_to_download:
            logger.info("所有模型都已安装")
            return
        
        logger.info(f"需要下载 {len(models_to_download)} 个模型")
        
        for model_name in models_to_download:
            self.download_model(model_name)
    
    def remove_model(self, model_name: str) -> bool:
        """删除指定模型"""
        if model_name not in self.model_configs:
            logger.error(f"未知的模型: {model_name}")
            return False
        
        model_path = self.models_dir / self.model_configs[model_name]['path']
        
        if not model_path.exists():
            logger.warning(f"模型 {model_name} 不存在")
            return True
        
        try:
            model_path.unlink()
            logger.success(f"模型 {model_name} 已删除")
            return True
        except Exception as e:
            logger.error(f"删除模型 {model_name} 失败: {e}")
            return False
    
    def verify_models(self) -> None:
        """验证已安装的模型"""
        print("\n验证模型完整性:")
        print("=" * 40)
        
        for name, config in self.model_configs.items():
            if self.is_model_installed(name):
                model_path = self.models_dir / config['path']
                size = model_path.stat().st_size
                size_mb = size / (1024 * 1024)
                
                print(f"{name}: ✓ ({size_mb:.1f}MB)")
            else:
                print(f"{name}: ✗ (未安装)")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI模型下载和管理工具')
    parser.add_argument('action', choices=['list', 'download', 'download-all', 'remove', 'verify'],
                       help='操作类型')
    parser.add_argument('--model', '-m', help='模型名称')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新下载')
    parser.add_argument('--required-only', '-r', action='store_true', help='仅下载必需的模型')
    
    args = parser.parse_args()
    
    downloader = ModelDownloader()
    
    if args.action == 'list':
        downloader.list_models()
    
    elif args.action == 'download':
        if not args.model:
            print("错误: 请指定模型名称 (--model)")
            sys.exit(1)
        downloader.download_model(args.model, args.force)
    
    elif args.action == 'download-all':
        downloader.download_all_models(args.required_only)
    
    elif args.action == 'remove':
        if not args.model:
            print("错误: 请指定模型名称 (--model)")
            sys.exit(1)
        downloader.remove_model(args.model)
    
    elif args.action == 'verify':
        downloader.verify_models()


if __name__ == '__main__':
    main()