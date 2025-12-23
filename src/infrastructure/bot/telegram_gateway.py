"""
Telegram Bot Gateway
IBotGateway implementasyonu
"""

import os
from typing import Optional
import logging

from telegram import Bot

from ...domain import IBotGateway, ImageEntity, BotGatewayError

logger = logging.getLogger(__name__)


class TelegramBotGateway(IBotGateway):
    """
    Telegram bot iletişim gateway'i.
    IBotGateway interface'ini implement eder.
    """
    
    def __init__(self, token: str):
        self.token = token
        self._bot: Optional[Bot] = None
    
    @property
    def bot(self) -> Bot:
        """Lazy bot instance"""
        if not self._bot:
            self._bot = Bot(token=self.token)
        return self._bot
    
    async def send_message(self, chat_id: str, text: str) -> None:
        """Mesaj gönder"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mesaj gönderilemedi: {e}")
            raise BotGatewayError("Mesaj gönderilemedi", details=str(e))
    
    async def send_image(
        self,
        chat_id: str,
        image: ImageEntity,
        caption: Optional[str] = None
    ) -> None:
        """Görsel gönder"""
        try:
            if not image.exists:
                raise BotGatewayError(f"Görsel bulunamadı: {image.path}")
            
            with open(image.path, 'rb') as f:
                # Hem doküman hem önizleme olarak gönder
                await self.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=image.filename,
                    caption=caption,
                    parse_mode="Markdown"
                )
            
            with open(image.path, 'rb') as f:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=f"👆 _Önizleme_",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Görsel gönderilemedi: {e}")
            raise BotGatewayError("Görsel gönderilemedi", details=str(e))
    
    async def update_message(self, chat_id: str, message_id: str, text: str) -> None:
        """Mevcut mesajı güncelle"""
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.debug(f"Mesaj güncellenemedi: {e}")
    
    async def download_file(self, file_id: str, destination: str) -> str:
        """Bot'a gönderilen dosyayı indir"""
        try:
            file = await self.bot.get_file(file_id)
            await file.download_to_drive(destination)
            return destination
        except Exception as e:
            logger.error(f"Dosya indirilemedi: {e}")
            raise BotGatewayError("Dosya indirilemedi", details=str(e))
