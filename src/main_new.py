import asyncio
import logging
from src.container import container
from src.domain.entities import ProcessContext, ImageEntity
import config

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s"
)
logger = logging.getLogger("Main")

async def main():
    logger.info("🤖 Modern AI Görsel Otomasyon Sistemi Başlatıldı (Clean Architecture)")
    
    # Not: Burada gerçek bir Telegram botu polling'i başlayacak
    # Mevcut yapıyı simüle eden bir örnek akış:
    chat_id = "USER_CHAT_ID" # Gerçek handler'dan gelecek
    
    # 1. Telegram bot gateway'i üzerinden yeni mesajın yakalandığını varsayalım
    # bot_gateway.polling() ...
    
    logger.info("Bot durduruldu.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
