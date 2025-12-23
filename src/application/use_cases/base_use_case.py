"""
Application - Base Use Case
Tüm use case'lerin türetilmesi gereken abstract base class.
OCP: Yeni use case = BaseUseCase'den türet, get_metadata() implement et.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
import logging

from ...core.use_case_registry import UseCaseMetadata

logger = logging.getLogger(__name__)

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class BaseUseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base Use Case - Abstract Base Class.
    
    Tüm use case'ler bu sınıftan türetilmeli ve:
    1. get_metadata() class metodunu implement etmeli
    2. execute() metodunu implement etmeli
    
    Registry tarafından otomatik keşfedilir.
    
    Örnek:
        class AnalyzeImageUseCase(BaseUseCase[ImageAnalysisRequest, str]):
            @classmethod
            def get_metadata(cls) -> UseCaseMetadata:
                return UseCaseMetadata(
                    name="analyze_image",
                    requires_browser=True,
                    requires_ai=True,
                )
            
            async def execute(self, request: ImageAnalysisRequest, **kwargs) -> str:
                ...
    """
    
    @classmethod
    @abstractmethod
    def get_metadata(cls) -> UseCaseMetadata:
        """
        Use case metadata'sını döndür.
        Auto-discovery için zorunlu.
        
        Returns:
            UseCaseMetadata instance
        """
        pass
    
    @abstractmethod
    async def execute(self, request: TRequest, **kwargs) -> TResponse:
        """
        Use case'i çalıştır.
        
        Args:
            request: Giriş isteği
            **kwargs: Ek parametreler (progress_notifier vb.)
            
        Returns:
            İşlem sonucu
        """
        pass
    
    def validate_request(self, request: TRequest) -> None:
        """
        İsteği doğrula. Alt sınıflar override edebilir.
        
        Args:
            request: Doğrulanacak istek
            
        Raises:
            ValidationError: Doğrulama başarısız
        """
        pass
    
    @property
    def name(self) -> str:
        """Use case adı"""
        return self.get_metadata().name
    
    def __repr__(self) -> str:
        meta = self.get_metadata()
        return f"<{self.__class__.__name__} name='{meta.name}' v{meta.version}>"
