"""
Core - Use Case Registry
Use case'lerin otomatik keşfi ve yönetimi için registry.
OCP: Yeni use case = yeni dosya, mevcut koda dokunma yok.
"""

from typing import Type, Optional, Dict, Any
import logging

from .registry import PluginRegistry, PluginMetadata

logger = logging.getLogger(__name__)


class UseCaseMetadata(PluginMetadata):
    """Use case'e özgü metadata"""
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        requires_browser: bool = False,
        requires_ai: bool = False,
        is_async: bool = True,
        **kwargs
    ):
        super().__init__(
            name=name,
            version=version,
            description=description,
            **kwargs
        )
        self.requires_browser = requires_browser
        self.requires_ai = requires_ai
        self.is_async = is_async


# Forward declaration için TYPE_CHECKING kullanılacak
# BaseUseCase application katmanında tanımlanacak


class UseCaseRegistry(PluginRegistry):
    """
    Use Case Registry - OCP Uyumlu.
    
    Use case'leri otomatik keşfeder ve yönetir.
    
    Kullanım:
        registry = get_use_case_registry()
        registry.discover()
        
        analyze_uc = registry.get("analyze_image", ai_service=ai, browser=browser)
        result = await analyze_uc.execute(request)
    """
    
    _instance: Optional["UseCaseRegistry"] = None
    
    def __init__(self):
        super().__init__()
        self._base_class = None  # Lazy load to avoid circular import
    
    def _get_plugin_package(self) -> str:
        return "src.application.use_cases"
    
    def _get_base_class(self) -> Type:
        if self._base_class is None:
            # Lazy import to avoid circular dependency
            from ..application.use_cases.base_use_case import BaseUseCase
            self._base_class = BaseUseCase
        return self._base_class
    
    def get_by_capability(
        self, 
        requires_browser: bool = False,
        requires_ai: bool = False,
        **kwargs
    ) -> list:
        """
        Belirli yeteneklere sahip use case'leri getir.
        
        Args:
            requires_browser: Browser gerektiren use case'ler
            requires_ai: AI gerektiren use case'ler
            
        Returns:
            Eşleşen use case listesi
        """
        matches = []
        for name, meta in self._metadata.items():
            if isinstance(meta, UseCaseMetadata):
                if requires_browser and not meta.requires_browser:
                    continue
                if requires_ai and not meta.requires_ai:
                    continue
                matches.append(self.get(name, **kwargs))
        return matches
    
    @classmethod
    def get_instance(cls) -> "UseCaseRegistry":
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


def get_use_case_registry() -> UseCaseRegistry:
    """Use Case Registry instance al"""
    return UseCaseRegistry.get_instance()
