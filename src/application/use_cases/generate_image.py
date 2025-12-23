"""
Use Case: Görsel Oluşturma
Tek sorumluluk: Prompt'tan görsel oluştur
"""

from typing import Optional, List
import logging

from ...domain import (
    IAIService,
    IProgressNotifier,
    ImageEntity,
    ProcessStatus,
    ImageGenerationError,
)

logger = logging.getLogger(__name__)


class GenerateImageUseCase:
    """
    Görsel oluşturma kullanım durumu.
    SOLID - Tek Sorumluluk: Sadece görsel oluşturur.
    """
    
    def __init__(self, ai_service: IAIService):
        self.ai_service = ai_service
    
    async def execute(
        self,
        prompt: str,
        count: int = 1,
        progress_notifier: Optional[IProgressNotifier] = None,
    ) -> List[ImageEntity]:
        """
        Prompt'tan görsel(ler) oluştur.
        
        Args:
            prompt: Görsel oluşturma prompt'u
            count: Oluşturulacak görsel sayısı
            progress_notifier: İlerleme bildirici (opsiyonel)
        
        Returns:
            Oluşturulan görsellerin listesi
        
        Raises:
            ImageGenerationError: Oluşturma başarısız olduğunda
        """
        logger.info(f"{count} görsel oluşturulacak")
        
        generated_images: List[ImageEntity] = []
        
        for i in range(1, count + 1):
            try:
                if progress_notifier:
                    await progress_notifier.notify_image_progress(i, count)
                    await progress_notifier.notify_step(
                        ProcessStatus.GENERATING,
                        f"Görsel {i}/{count} oluşturuluyor..."
                    )
                
                # Yeni oturum başlat (her görsel için)
                self.ai_service.start_new_session()
                
                # Görsel oluştur
                image = self.ai_service.generate_image(prompt)
                generated_images.append(image)
                
                logger.info(f"Görsel {i}/{count} oluşturuldu: {image.path}")
                
            except Exception as e:
                logger.error(f"Görsel {i} oluşturulamadı: {e}")
                # Devam et, diğer görselleri dene
                continue
        
        if not generated_images:
            raise ImageGenerationError(
                "Hiçbir görsel oluşturulamadı",
                details=f"Hedef: {count} görsel"
            )
        
        return generated_images
