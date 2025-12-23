"""
Core - Generic Plugin Registry
Tüm plugin sistemlerinin temel sınıfı.
Open-Closed Principle: Yeni plugin = yeni dosya, mevcut koda dokunma yok.
"""

from abc import ABC, abstractmethod
from typing import (
    Generic, TypeVar, Dict, List, Callable, Optional, Type, Set, Any
)
from dataclasses import dataclass, field
import logging
import importlib
import pkgutil
from pathlib import Path

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass(frozen=True)
class PluginMetadata:
    """Plugin meta bilgileri"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    supported_features: Set[str] = field(default_factory=set)
    priority: int = 0  # Yüksek = daha öncelikli
    
    def supports(self, feature: str) -> bool:
        """Belirtilen özelliği destekliyor mu?"""
        return feature in self.supported_features


class PluginRegistry(Generic[T], ABC):
    """
    Generic Plugin Registry.
    
    OCP Uyumu: Yeni plugin eklemek için sadece:
    1. Yeni sınıf oluştur
    2. get_metadata() metodunu implement et
    3. plugins/ klasörüne koy
    
    Mevcut koda dokunmaya gerek yok.
    """
    
    def __init__(self):
        self._plugins: Dict[str, Type[T]] = {}
        self._instances: Dict[str, T] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
    
    @abstractmethod
    def _get_plugin_package(self) -> str:
        """Plugin'lerin bulunduğu package path'i"""
        pass
    
    @abstractmethod
    def _get_base_class(self) -> Type[T]:
        """Plugin'lerin türetilmesi gereken base class"""
        pass
    
    def register(self, plugin_class: Type[T]) -> None:
        """
        Plugin'i registry'ye kaydet.
        
        Args:
            plugin_class: Kaydedilecek plugin sınıfı
        """
        if not hasattr(plugin_class, 'get_metadata'):
            raise ValueError(f"{plugin_class.__name__} get_metadata() metoduna sahip değil")
        
        metadata: PluginMetadata = plugin_class.get_metadata()
        name = metadata.name
        
        if name in self._plugins:
            logger.warning(f"Plugin '{name}' zaten kayıtlı, üzerine yazılıyor")
        
        self._plugins[name] = plugin_class
        self._metadata[name] = metadata
        logger.info(f"Plugin kaydedildi: {name} (v{metadata.version})")
    
    def discover(self) -> int:
        """
        Plugin'leri otomatik keşfet ve kaydet.
        
        Returns:
            Keşfedilen plugin sayısı
        """
        package_path = self._get_plugin_package()
        base_class = self._get_base_class()
        discovered_count = 0
        
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent
            
            for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
                if module_name.startswith('_'):
                    continue
                
                try:
                    module = importlib.import_module(f"{package_path}.{module_name}")
                    
                    # Modüldeki tüm sınıfları tara
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        if (isinstance(attr, type) and 
                            issubclass(attr, base_class) and 
                            attr is not base_class and
                            hasattr(attr, 'get_metadata')):
                            
                            self.register(attr)
                            discovered_count += 1
                            
                except Exception as e:
                    logger.warning(f"Modül yüklenemedi: {module_name} - {e}")
                    
        except ImportError as e:
            logger.error(f"Plugin package bulunamadı: {package_path} - {e}")
        
        logger.info(f"Toplam {discovered_count} plugin keşfedildi")
        return discovered_count
    
    def get(self, name: str, **kwargs) -> T:
        """
        Plugin instance al (lazy init).
        
        Args:
            name: Plugin adı
            **kwargs: Plugin constructor argümanları
            
        Returns:
            Plugin instance
        """
        if name not in self._plugins:
            available = list(self._plugins.keys())
            raise KeyError(f"Plugin bulunamadı: '{name}'. Mevcut: {available}")
        
        # Cache'den al veya oluştur
        cache_key = f"{name}:{hash(frozenset(kwargs.items()))}"
        
        if cache_key not in self._instances:
            plugin_class = self._plugins[name]
            self._instances[cache_key] = plugin_class(**kwargs)
            logger.debug(f"Plugin instance oluşturuldu: {name}")
        
        return self._instances[cache_key]
    
    def get_by_feature(self, feature: str, **kwargs) -> Optional[T]:
        """
        Belirtilen özelliği destekleyen en öncelikli plugin'i al.
        
        Args:
            feature: İstenen özellik
            **kwargs: Plugin constructor argümanları
            
        Returns:
            Plugin instance veya None
        """
        candidates = [
            (name, meta) 
            for name, meta in self._metadata.items() 
            if meta.supports(feature)
        ]
        
        if not candidates:
            return None
        
        # Önceliğe göre sırala
        candidates.sort(key=lambda x: x[1].priority, reverse=True)
        best_name = candidates[0][0]
        
        return self.get(best_name, **kwargs)
    
    def list_plugins(self) -> List[str]:
        """Kayıtlı plugin isimlerini listele"""
        return list(self._plugins.keys())
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Plugin meta bilgilerini al"""
        return self._metadata.get(name)
    
    def clear(self) -> None:
        """Registry'yi temizle (test için)"""
        self._plugins.clear()
        self._instances.clear()
        self._metadata.clear()
