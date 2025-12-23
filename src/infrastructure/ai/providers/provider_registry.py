"""
AI Provider Registry
AI provider'ların otomatik keşfi ve yönetimi.
"""

import logging
from typing import Type, Optional

from ....core import PluginRegistry
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class AIProviderRegistry(PluginRegistry[BaseAIProvider]):
    """
    AI Provider Registry.
    
    OCP Uyumu: Yeni AI provider eklemek için:
    1. providers/ klasörüne yeni provider sınıfı ekle
    2. BaseAIProvider'dan türet
    3. get_metadata() implement et
    
    registry.discover() otomatik olarak bulup kaydedecek.
    """
    
    _instance: Optional["AIProviderRegistry"] = None
    
    def _get_plugin_package(self) -> str:
        """Provider'ların bulunduğu package"""
        return "src.infrastructure.ai.providers"
    
    def _get_base_class(self) -> Type[BaseAIProvider]:
        """Provider base class"""
        return BaseAIProvider
    
    @classmethod
    def get_instance(cls) -> "AIProviderRegistry":
        """Singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Registry'yi sıfırla (test için)"""
        if cls._instance:
            cls._instance.clear()
        cls._instance = None
    
    def get_default_provider(self, **kwargs) -> BaseAIProvider:
        """
        Varsayılan (en yüksek öncelikli) provider'ı al.
        
        Returns:
            BaseAIProvider instance
        """
        if not self._plugins:
            raise RuntimeError("Hiç AI provider kayıtlı değil. discover() çağrıldı mı?")
        
        # Önceliğe göre sırala
        sorted_by_priority = sorted(
            self._metadata.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        best_name = sorted_by_priority[0][0]
        return self.get(best_name, **kwargs)
    
    def get_for_analysis(self, **kwargs) -> Optional[BaseAIProvider]:
        """Görsel analizi destekleyen provider al"""
        return self.get_by_feature("analyze", **kwargs)
    
    def get_for_generation(self, **kwargs) -> Optional[BaseAIProvider]:
        """Görsel oluşturma destekleyen provider al"""
        return self.get_by_feature("generate", **kwargs)


# Global registry instance getter
def get_ai_registry() -> AIProviderRegistry:
    """AI Provider Registry instance al"""
    return AIProviderRegistry.get_instance()
