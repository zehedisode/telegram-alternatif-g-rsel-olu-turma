"""
Use Case: Görsel Analizi
Tek sorumluluk: Görseli AI ile analiz et ve prompt çıkar
"""

from typing import Optional
import logging

from ...domain import (
    IAIService,
    IBrowserService,
    IProgressNotifier,
    ImageEntity,
    ProcessStatus,
    AIServiceError,
)

logger = logging.getLogger(__name__)


class AnalyzeImageUseCase:
    """
    Görsel analizi kullanım durumu.
    SOLID - Tek Sorumluluk: Sadece görsel analizi yapar.
    """
    
    def __init__(
        self,
        ai_service: IAIService,
        browser_service: IBrowserService,
    ):
        self.ai_service = ai_service
        self.browser_service = browser_service
    
    async def execute(
        self,
        image: ImageEntity,
        system_prompt: str,
        progress_notifier: Optional[IProgressNotifier] = None,
    ) -> str:
        """
        Görseli analiz et ve prompt döndür.
        
        Args:
            image: Analiz edilecek görsel
            system_prompt: Sistem prompt'u
            progress_notifier: İlerleme bildirici (opsiyonel)
        
        Returns:
            Çıkarılan prompt metni
        
        Raises:
            AIServiceError: Analiz başarısız olduğunda
        """
        logger.info(f"Görsel analizi başlatılıyor: {image.path}")
        
        try:
            # Tarayıcı başlat
            if progress_notifier:
                await progress_notifier.notify_step(
                    ProcessStatus.BROWSER_STARTING, 
                    "Tarayıcı başlatılıyor..."
                )
            
            if not self.browser_service.is_running():
                self.browser_service.start()
            
            # Analiz yap
            if progress_notifier:
                await progress_notifier.notify_step(
                    ProcessStatus.ANALYZING, 
                    "Görsel analiz ediliyor..."
                )
            
            extracted_prompt = self.ai_service.analyze_image(image, system_prompt)
            
            if progress_notifier:
                await progress_notifier.notify_step(
                    ProcessStatus.PROMPT_RECEIVED, 
                    "Prompt alındı"
                )
            
            logger.info(f"Prompt çıkarıldı: {extracted_prompt[:100]}...")
            return extracted_prompt
            
        except Exception as e:
            logger.error(f"Görsel analizi başarısız: {e}")
            raise AIServiceError("Görsel analizi başarısız", details=str(e))
