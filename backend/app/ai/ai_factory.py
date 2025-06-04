#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI工厂模块
管理和创建不同的AI提供商实例
"""

from typing import Dict, Optional, Any, List
from loguru import logger

from .ai_interface import AIInterface, AIProvider, MockAIProvider, AIProviderInfo, AICapabilities
from ..core.config import settings
from ..core.exceptions import BaseStockException


class AIProviderRegistry:
    """AI提供商注册表"""
    
    def __init__(self):
        self._providers: Dict[AIProvider, type] = {}
        self._provider_configs: Dict[AIProvider, Dict[str, Any]] = {}
        self._provider_info: Dict[AIProvider, AIProviderInfo] = {}
        self._register_default_providers()
    
    def _register_default_providers(self):
        """注册默认的AI提供商"""
        # 注册Mock提供商
        self.register_provider(
            AIProvider.MOCK,
            MockAIProvider,
            {
                "name": "Mock AI Provider",
                "description": "用于测试和开发的模拟AI提供商",
                "capabilities": [
                    AICapabilities.TEXT_GENERATION,
                    AICapabilities.SENTIMENT_ANALYSIS,
                    AICapabilities.KEYWORD_EXTRACTION
                ],
                "max_tokens": 2000,
                "cost_per_token": 0.0
            }
        )
        
        # 可以在这里注册其他提供商
        # self._register_openai_provider()
        # self._register_claude_provider()
        # self._register_qwen_provider()
    
    def register_provider(self, provider: AIProvider, provider_class: type, config: Dict[str, Any]):
        """注册AI提供商"""
        self._providers[provider] = provider_class
        self._provider_configs[provider] = config
        
        # 创建提供商信息
        self._provider_info[provider] = AIProviderInfo(
            name=config.get("name", provider.value),
            provider=provider,
            capabilities=config.get("capabilities", []),
            max_tokens=config.get("max_tokens", 1000),
            cost_per_token=config.get("cost_per_token"),
            rate_limit=config.get("rate_limit"),
            description=config.get("description")
        )
        
        logger.info(f"注册AI提供商: {provider.value}")
    
    def get_provider_class(self, provider: AIProvider) -> Optional[type]:
        """获取提供商类"""
        return self._providers.get(provider)
    
    def get_provider_config(self, provider: AIProvider) -> Optional[Dict[str, Any]]:
        """获取提供商配置"""
        return self._provider_configs.get(provider)
    
    def get_provider_info(self, provider: AIProvider) -> Optional[AIProviderInfo]:
        """获取提供商信息"""
        return self._provider_info.get(provider)
    
    def list_providers(self) -> List[AIProviderInfo]:
        """列出所有注册的提供商"""
        return list(self._provider_info.values())
    
    def get_providers_by_capability(self, capability: str) -> List[AIProvider]:
        """根据能力获取提供商"""
        providers = []
        for provider, info in self._provider_info.items():
            if capability in info.capabilities:
                providers.append(provider)
        return providers


class AIFactory:
    """AI工厂类"""
    
    def __init__(self):
        self.registry = AIProviderRegistry()
        self._instances: Dict[AIProvider, AIInterface] = {}
        self._default_provider = AIProvider.MOCK
    
    def set_default_provider(self, provider: AIProvider):
        """设置默认提供商"""
        if provider not in self.registry._providers:
            raise BaseStockException(f"未注册的AI提供商: {provider.value}")
        
        self._default_provider = provider
        logger.info(f"设置默认AI提供商: {provider.value}")
    
    async def get_provider(self, provider: Optional[AIProvider] = None) -> AIInterface:
        """获取AI提供商实例"""
        if provider is None:
            provider = self._default_provider
        
        # 如果已经有实例，直接返回
        if provider in self._instances:
            instance = self._instances[provider]
            if instance.is_initialized:
                return instance
        
        # 创建新实例
        instance = await self._create_provider_instance(provider)
        self._instances[provider] = instance
        
        return instance
    
    async def _create_provider_instance(self, provider: AIProvider) -> AIInterface:
        """创建提供商实例"""
        provider_class = self.registry.get_provider_class(provider)
        if not provider_class:
            raise BaseStockException(f"未找到AI提供商实现: {provider.value}")
        
        provider_config = self.registry.get_provider_config(provider) or {}
        
        try:
            # 创建实例
            if provider == AIProvider.MOCK:
                instance = provider_class(provider_config)
            else:
                # 其他提供商可能需要不同的初始化参数
                instance = provider_class(provider, self._get_provider_runtime_config(provider))
            
            # 初始化
            success = await instance.initialize()
            if not success:
                raise BaseStockException(f"AI提供商初始化失败: {provider.value}")
            
            logger.info(f"AI提供商创建成功: {provider.value}")
            return instance
            
        except Exception as e:
            logger.error(f"创建AI提供商失败 {provider.value}: {str(e)}")
            raise BaseStockException(f"创建AI提供商失败: {str(e)}")
    
    def _get_provider_runtime_config(self, provider: AIProvider) -> Dict[str, Any]:
        """获取提供商运行时配置"""
        config = {}
        
        if provider == AIProvider.OPENAI:
            config = {
                "api_key": getattr(settings, "OPENAI_API_KEY", ""),
                "base_url": getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "model": getattr(settings, "OPENAI_MODEL", "gpt-3.5-turbo")
            }
        elif provider == AIProvider.CLAUDE:
            config = {
                "api_key": getattr(settings, "CLAUDE_API_KEY", ""),
                "model": getattr(settings, "CLAUDE_MODEL", "claude-3-sonnet-20240229")
            }
        elif provider == AIProvider.QWEN:
            config = {
                "api_key": getattr(settings, "QWEN_API_KEY", ""),
                "model": getattr(settings, "QWEN_MODEL", "qwen-turbo")
            }
        elif provider == AIProvider.BAIDU:
            config = {
                "api_key": getattr(settings, "BAIDU_API_KEY", ""),
                "secret_key": getattr(settings, "BAIDU_SECRET_KEY", ""),
                "model": getattr(settings, "BAIDU_MODEL", "ernie-bot")
            }
        
        return config
    
    async def get_best_provider_for_capability(self, capability: str) -> AIInterface:
        """获取特定能力的最佳提供商"""
        providers = self.registry.get_providers_by_capability(capability)
        
        if not providers:
            logger.warning(f"没有找到支持 {capability} 的AI提供商，使用默认提供商")
            return await self.get_provider()
        
        # 简单的选择策略：优先选择非Mock提供商
        for provider in providers:
            if provider != AIProvider.MOCK:
                try:
                    return await self.get_provider(provider)
                except Exception as e:
                    logger.warning(f"提供商 {provider.value} 不可用: {str(e)}")
                    continue
        
        # 如果其他提供商都不可用，使用Mock提供商
        return await self.get_provider(AIProvider.MOCK)
    
    async def health_check_all(self) -> Dict[AIProvider, bool]:
        """检查所有提供商的健康状态"""
        results = {}
        
        for provider in self.registry._providers.keys():
            try:
                instance = await self.get_provider(provider)
                is_healthy = await instance.health_check()
                results[provider] = is_healthy
            except Exception as e:
                logger.error(f"健康检查失败 {provider.value}: {str(e)}")
                results[provider] = False
        
        return results
    
    def get_provider_info(self, provider: AIProvider) -> Optional[AIProviderInfo]:
        """获取提供商信息"""
        return self.registry.get_provider_info(provider)
    
    def list_available_providers(self) -> List[AIProviderInfo]:
        """列出所有可用的提供商"""
        return self.registry.list_providers()
    
    async def switch_provider(self, new_provider: AIProvider) -> bool:
        """切换默认提供商"""
        try:
            # 测试新提供商是否可用
            instance = await self.get_provider(new_provider)
            is_healthy = await instance.health_check()
            
            if is_healthy:
                self.set_default_provider(new_provider)
                logger.info(f"成功切换到AI提供商: {new_provider.value}")
                return True
            else:
                logger.error(f"AI提供商健康检查失败: {new_provider.value}")
                return False
                
        except Exception as e:
            logger.error(f"切换AI提供商失败: {str(e)}")
            return False
    
    def clear_instances(self):
        """清除所有实例（用于重新初始化）"""
        self._instances.clear()
        logger.info("清除所有AI提供商实例")


# 全局AI工厂实例
ai_factory = AIFactory()


# 便捷函数
async def get_ai_provider(provider: Optional[AIProvider] = None) -> AIInterface:
    """获取AI提供商实例的便捷函数"""
    return await ai_factory.get_provider(provider)


async def get_recommendation_explainer() -> 'RecommendationExplainer':
    """获取推荐解释器"""
    from .recommendation_explainer import RecommendationExplainer
    
    ai_provider = await get_ai_provider()
    return RecommendationExplainer(ai_provider)


async def get_market_analyzer() -> 'MarketAnalyzer':
    """获取市场分析器"""
    from .market_analyzer import MarketAnalyzer
    
    ai_provider = await get_ai_provider()
    return MarketAnalyzer(ai_provider)


# AI配置管理
class AIConfigManager:
    """AI配置管理器"""
    
    @staticmethod
    def load_config_from_settings() -> Dict[str, Any]:
        """从设置中加载AI配置"""
        config = {
            "default_provider": getattr(settings, "AI_DEFAULT_PROVIDER", "mock"),
            "enabled_providers": getattr(settings, "AI_ENABLED_PROVIDERS", ["mock"]),
            "max_retries": getattr(settings, "AI_MAX_RETRIES", 3),
            "timeout": getattr(settings, "AI_TIMEOUT", 30),
            "rate_limit": getattr(settings, "AI_RATE_LIMIT", {"requests_per_minute": 60})
        }
        
        return config
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """验证AI配置"""
        required_fields = ["default_provider", "enabled_providers"]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"AI配置缺少必需字段: {field}")
                return False
        
        # 验证提供商名称
        valid_providers = [provider.value for provider in AIProvider]
        
        if config["default_provider"] not in valid_providers:
            logger.error(f"无效的默认AI提供商: {config['default_provider']}")
            return False
        
        for provider in config["enabled_providers"]:
            if provider not in valid_providers:
                logger.error(f"无效的AI提供商: {provider}")
                return False
        
        return True
    
    @staticmethod
    async def initialize_ai_factory_from_config():
        """从配置初始化AI工厂"""
        config = AIConfigManager.load_config_from_settings()
        
        if not AIConfigManager.validate_config(config):
            logger.warning("AI配置验证失败，使用默认配置")
            return
        
        try:
            # 设置默认提供商
            default_provider = AIProvider(config["default_provider"])
            ai_factory.set_default_provider(default_provider)
            
            logger.info("AI工厂初始化完成")
            
        except Exception as e:
            logger.error(f"AI工厂初始化失败: {str(e)}")


# 初始化函数
async def initialize_ai_system():
    """初始化AI系统"""
    try:
        await AIConfigManager.initialize_ai_factory_from_config()
        
        # 进行健康检查
        health_status = await ai_factory.health_check_all()
        
        healthy_providers = [provider.value for provider, is_healthy in health_status.items() if is_healthy]
        logger.info(f"可用的AI提供商: {healthy_providers}")
        
        if not any(health_status.values()):
            logger.warning("没有可用的AI提供商")
        
    except Exception as e:
        logger.error(f"AI系统初始化失败: {str(e)}")