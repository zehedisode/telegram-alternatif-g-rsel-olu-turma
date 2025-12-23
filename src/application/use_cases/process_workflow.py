"""
Use Case: Tam İş Akışı
Görsel analizi + Görsel oluşturma orkestratörü
"""

from typing import List, Optional
import logging
import time

from ...domain import (
    IAIService,
    IBrowserService,
    IBotGateway,
    IProgressNotifier,
    ImageEntity,
    SessionEntity,
    ProcessContext,
    ProcessStatus,
    DomainException,
)
from ..dtos import ImageProcessRequest, ImageProcessResult
from .analyze_image import AnalyzeImageUseCase
from .generate_image import GenerateImageUseCase

logger = logging.getLogger(__name__)


class ProcessImageWorkflowUseCase:
    """
    Tam iş akışı orkestrasyonu.
    SOLID - Tek Sorumluluk: Use case'leri koordine eder.
    """
    
    def __init__(
        self,
        ai_service: IAIService,
        browser_service: IBrowserService,
        bot_gateway: IBotGateway,
    ):
        self.ai_service = ai_service
        self.browser_service = browser_service
        self.bot_gateway = bot_gateway
        
        # Alt use case'ler - Composition
        self.analyze_use_case = AnalyzeImageUseCase(ai_service, browser_service)
        self.generate_use_case = GenerateImageUseCase(ai_service)
    
    async def execute(
        self,
        request: ImageProcessRequest,
        system_prompt: str,
        progress_notifier: Optional[IProgressNotifier] = None,
    ) -> ImageProcessResult:
        """
        Tam iş akışını çalıştır.
        
        Args:
            request: İşlem isteği
            system_prompt: Sistem prompt'u
            progress_notifier: İlerleme bildirici
        
        Returns:
            İşlem sonucu
        """
        start_time = time.time()
        
        # Context oluştur
        session = SessionEntity(chat_id=request.chat_id, user_id=request.user_id)
        original_image = ImageEntity(path=request.image_path)
        
        context = ProcessContext(
            session=session,
            original_image=original_image,
            target_count=request.target_count,
        )
        
        try:
            logger.info(f"İş akışı başlatılıyor: {session.session_id}")
            
            # 1. Analiz
            extracted_prompt = await self.analyze_use_case.execute(
                image=original_image,
                system_prompt=system_prompt,
                progress_notifier=progress_notifier,
            )
            context.extracted_prompt = extracted_prompt
            
            # 2. Görsel oluştur
            generated_images = await self.generate_use_case.execute(
                prompt=extracted_prompt,
                count=request.target_count,
                progress_notifier=progress_notifier,
            )
            
            # Sonuçları context'e ekle
            for img in generated_images:
                context.add_generated_image(img)
            
            context.mark_completed()
            
            # Sonuç DTO'su oluştur
            duration = int(time.time() - start_time)
            
            return ImageProcessResult(
                success=True,
                generated_image_paths=[img.path for img in generated_images],
                extracted_prompt=extracted_prompt,
                duration_seconds=duration,
            )
            
        except DomainException as e:
            logger.error(f"İş akışı hatası: {e}")
            context.mark_failed(str(e))
            
            duration = int(time.time() - start_time)
            return ImageProcessResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )
        
        finally:
            # Tarayıcıyı kapat
            try:
                self.browser_service.stop()
            except Exception as e:
                logger.warning(f"Tarayıcı kapatılırken hata: {e}")
