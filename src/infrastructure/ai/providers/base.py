"""
AI Provider Base Class
Tüm AI provider'ların türetilmesi gereken abstract base class.
OCP: Yeni AI = yeni provider sınıfı, mevcut koda dokunma yok.
"""

from abc import ABC, abstractmethod
from typing import Set, Optional
from dataclasses import dataclass, field

from ....core import PluginMetadata, Result
from ....domain import ImageEntity, AIServiceError


@dataclass(frozen=True)
class AIProviderMeta(PluginMetadata):
    """AI Provider'a özgü metadata"""
    supports_image_analysis: bool = True
    supports_image_generation: bool = True
    max_images_per_request: int = 4


class BaseAIProvider(ABC):
    """
    Base AI Provider.
    
    Yeni bir AI servisi eklemek için:
    1. Bu sınıftan türet
    2. get_metadata() class metodunu implement et
    3. analyze_image() ve generate_image() metodlarını implement et
    4. providers/ klasörüne koy
    
    Sistem otomatik olarak keşfedecek ve register edecek.
    """
    
    @classmethod
    @abstractmethod
    def get_metadata(cls) -> AIProviderMeta:
        """
        Provider metadata'sını döndür.
        Auto-discovery için zorunlu.
        """
        pass
    
    @abstractmethod
    def analyze_image(
        self, 
        image: ImageEntity, 
        prompt: str
    ) -> Result[str, AIServiceError]:
        """
        Görseli analiz et ve sonuç döndür.
        
        Args:
            image: Analiz edilecek görsel
            prompt: Analiz prompt'u
            
        Returns:
            Result[str, AIServiceError]: Başarı = analiz sonucu, Hata = AIServiceError
        """
        pass
    
    @abstractmethod
    def generate_image(
        self, 
        prompt: str
    ) -> Result[ImageEntity, AIServiceError]:
        """
        Prompt'tan görsel oluştur.
        
        Args:
            prompt: Görsel oluşturma prompt'u
            
        Returns:
            Result[ImageEntity, AIServiceError]: Başarı = oluşturulan görsel, Hata = AIServiceError
        """
        pass
    
    @abstractmethod
    def start_new_session(self) -> Result[None, AIServiceError]:
        """Yeni AI oturumu başlat"""
        pass
    
    def cleanup(self) -> None:
        """Kaynakları temizle (opsiyonel override)"""
        pass
