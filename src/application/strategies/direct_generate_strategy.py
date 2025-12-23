"""
Workflow Strategy: Direct Generate
Analiz olmadan doğrudan görsel oluşturma.
"""

import time
import logging

from ...domain import (
    IAIService,
    IBrowserService,
    ProcessStatus,
    DomainException,
)
from ..dtos import ImageProcessResult
from .base_strategy import WorkflowStrategy, WorkflowContext

logger = logging.getLogger(__name__)


class DirectGenerateStrategy(WorkflowStrategy):
    """
    Doğrudan Oluşturma Stratejisi.
    
    Akış:
    1. Kullanıcı prompt'u ile doğrudan görsel oluştur
    
    Analiz adımı atlanır - kullanıcı kendi prompt'unu sağlar.
    """
    
    def __init__(
        self,
        ai_service: IAIService,
        browser_service: IBrowserService,
    ):
        self.ai_service = ai_service
        self.browser_service = browser_service
    
    @classmethod
    def get_name(cls) -> str:
        return "direct_generate"
    
    @classmethod
    def get_description(cls) -> str:
        return "Kullanıcı prompt'u ile doğrudan görsel oluştur (analiz yok)"
    
    async def execute(self, context: WorkflowContext) -> ImageProcessResult:
        """Doğrudan generate akışını çalıştır"""
        start_time = time.time()
        
        # Prompt kontrolü
        if not context.system_prompt:
            return ImageProcessResult(
                success=False,
                error_message="DirectGenerateStrategy için prompt gerekli",
                duration_seconds=0,
            )
        
        try:
            logger.info(f"Strateji başlatılıyor: {self.get_name()}")
            
            # 1. Tarayıcı başlat
            await self._notify_progress(
                context,
                ProcessStatus.BROWSER_STARTING,
                "Tarayıcı başlatılıyor..."
            )
            
            if not self.browser_service.is_running():
                self.browser_service.start()
            
            # 2. Doğrudan görsel oluştur
            prompt = context.system_prompt
            context.extracted_prompt = prompt  # Kullanıcı prompt'u
            
            for i in range(context.request.target_count):
                await self._notify_progress(
                    context,
                    ProcessStatus.GENERATING,
                    f"Görsel oluşturuluyor ({i + 1}/{context.request.target_count})..."
                )
                
                generated_image = self.ai_service.generate_image(prompt)
                context.add_generated_image(generated_image)
                
                if context.progress_notifier:
                    await context.progress_notifier.notify_image_progress(
                        i + 1,
                        context.request.target_count
                    )
            
            # Sonuç
            duration = int(time.time() - start_time)
            
            return ImageProcessResult(
                success=True,
                generated_image_paths=[img.path for img in context.generated_images],
                extracted_prompt=prompt,
                duration_seconds=duration,
            )
            
        except DomainException as e:
            logger.error(f"Strateji hatası: {e}")
            duration = int(time.time() - start_time)
            
            return ImageProcessResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )
        
        finally:
            try:
                self.browser_service.stop()
            except Exception as e:
                logger.warning(f"Tarayıcı kapatılırken hata: {e}")
    
    async def _notify_progress(
        self,
        context: WorkflowContext,
        status: ProcessStatus,
        message: str
    ) -> None:
        """İlerleme bildirimi gönder"""
        if context.progress_notifier:
            await context.progress_notifier.notify_step(status, message)
