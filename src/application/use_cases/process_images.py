from typing import List, Optional
from ...domain.entities import ImageEntity, ProcessContext, ProcessStatus
from ...domain.interfaces import IAIService, IBotGateway

class GenerateImagesUseCase:
    """
    Kullanım Durumu: Görsel Analizi ve Yeni Görsel Oluşturma
    Bu sınıf sadece iş mantığını yönetir, dış bağımlılıklara (Telegram, Selenium) doğrudan dokunmaz.
    """
    def __init__(self, ai_service: IAIService, bot_gateway: IBotGateway):
        self.ai_service = ai_service
        self.bot_gateway = bot_gateway

    async def execute(self, chat_id: str, context: ProcessContext, system_prompt: str) -> List[ImageEntity]:
        try:
            # 1. Analiz
            context.status = ProcessStatus.ANALYZING
            await self.bot_gateway.send_message(chat_id, "🧠 Görsel analiz ediliyor...")
            extracted_prompt = self.ai_service.analyze_image(context.original_image, system_prompt)
            context.extracted_prompt = extracted_prompt

            # 2. Üretim
            context.status = ProcessStatus.GENERATING
            for i in range(context.target_count):
                await self.bot_gateway.send_message(chat_id, f"🎨 Görsel {i+1}/{context.target_count} oluşturuluyor...")
                generated_image = self.ai_service.generate_image(extracted_prompt)
                context.generated_images.append(generated_image)
                await self.bot_gateway.send_image(chat_id, generated_image, f"Görsel {i+1} hazır!")

            context.status = ProcessStatus.COMPLETED
            return context.generated_images

        except Exception as e:
            context.status = ProcessStatus.FAILED
            context.error_message = str(e)
            await self.bot_gateway.send_message(chat_id, f"❌ İşlem sırasında hata oluştu: {str(e)}")
            raise
