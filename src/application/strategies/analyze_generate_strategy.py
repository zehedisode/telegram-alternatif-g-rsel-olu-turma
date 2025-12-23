"""
Workflow Strategy: Analyze and Generate
Varsayılan iş akışı - önce analiz et, sonra görsel oluştur.
"""

import time
import logging
from typing import TYPE_CHECKING

from ...domain import (
    IAIService,
    IBrowserService,
    ImageEntity,
    ProcessStatus,
    DomainException,
)
from ..dtos import ImageProcessResult
from .base_strategy import WorkflowStrategy, WorkflowContext

if TYPE_CHECKING:
    from ..use_cases import AnalyzeImageUseCase, GenerateImageUseCase

logger = logging.getLogger(__name__)


class AnalyzeAndGenerateStrategy(WorkflowStrategy):
    """
    Analiz ve Oluşturma Stratejisi.
    
    Akış:
    1. Görseli analiz et → Prompt çıkar
    2. Çıkarılan prompt ile yeni görseller oluştur
    
    Bu varsayılan stratejidir.
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
        return "analyze_and_generate"
    
    @classmethod
    def get_description(cls) -> str:
        return "Görseli analiz et, prompt çıkar, yeni görseller oluştur"
    
    async def execute(self, context: WorkflowContext) -> ImageProcessResult:
        """Analiz → Generate akışını çalıştır"""
        start_time = time.time()
        
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
            
            # 2. Analiz
            await self._notify_progress(
                context,
                ProcessStatus.ANALYZING,
                "Görsel analiz ediliyor..."
            )
            
            extracted_prompt = self.ai_service.analyze_image(
                context.original_image,
                context.system_prompt
            )
            context.extracted_prompt = extracted_prompt
            
            await self._notify_progress(
                context,
                ProcessStatus.PROMPT_RECEIVED,
                "Prompt alındı"
            )
            
            # 3. Görsel oluşturma
            for i in range(context.request.target_count):
                await self._notify_progress(
                    context,
                    ProcessStatus.GENERATING,
                    f"Görsel oluşturuluyor ({i + 1}/{context.request.target_count})..."
                )
                
                generated_image = self.ai_service.generate_image(extracted_prompt)
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
                extracted_prompt=extracted_prompt,
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
            # Tarayıcıyı kapat
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
