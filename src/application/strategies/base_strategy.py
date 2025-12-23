"""
Application - Base Workflow Strategy
İş akışı stratejileri için abstract base class.
OCP: Yeni iş akışı = yeni strateji sınıfı, mevcut koda dokunma yok.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging

from ...domain import (
    ImageEntity,
    SessionEntity,
    ProcessContext,
    IProgressNotifier,
)
from ..dtos import ImageProcessRequest, ImageProcessResult

logger = logging.getLogger(__name__)


@dataclass
class WorkflowContext:
    """
    Workflow işlem bağlamı.
    Strateji boyunca taşınan durum bilgisi.
    """
    request: ImageProcessRequest
    session: SessionEntity
    original_image: ImageEntity
    system_prompt: str
    progress_notifier: Optional[IProgressNotifier] = None
    
    # Ara sonuçlar
    extracted_prompt: Optional[str] = None
    generated_images: List[ImageEntity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_generated_image(self, image: ImageEntity) -> None:
        """Oluşturulan görsel ekle"""
        self.generated_images.append(image)
    
    @property
    def completed_count(self) -> int:
        """Tamamlanan görsel sayısı"""
        return len(self.generated_images)


class WorkflowStrategy(ABC):
    """
    Base Workflow Strategy - Abstract Base Class.
    
    Farklı iş akışları için strateji pattern.
    OCP: Yeni akış = yeni strateji sınıfı.
    
    Mevcut stratejiler:
    - AnalyzeAndGenerateStrategy: Analiz → Generate (varsayılan)
    - DirectGenerateStrategy: Doğrudan generate (analiz olmadan)
    
    Yeni strateji eklemek için:
    1. Bu sınıftan türet
    2. get_name() ve execute() implement et
    3. strategies/ klasörüne koy
    """
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """
        Strateji adı.
        Registry'de benzersiz tanımlayıcı olarak kullanılır.
        """
        pass
    
    @classmethod
    def get_description(cls) -> str:
        """Strateji açıklaması (opsiyonel)"""
        return ""
    
    @abstractmethod
    async def execute(self, context: WorkflowContext) -> ImageProcessResult:
        """
        İş akışını çalıştır.
        
        Args:
            context: Workflow bağlamı
            
        Returns:
            İşlem sonucu
        """
        pass
    
    async def on_before_execute(self, context: WorkflowContext) -> None:
        """Execute öncesi hook (opsiyonel override)"""
        pass
    
    async def on_after_execute(
        self, 
        context: WorkflowContext, 
        result: ImageProcessResult
    ) -> None:
        """Execute sonrası hook (opsiyonel override)"""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.get_name()}'>"
