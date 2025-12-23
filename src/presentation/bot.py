"""
Bot Entry Point
Telegram bot'unu başlatan ve yapılandıran modül
"""

import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from .handlers import (
    start_handler,
    status_handler,
    cancel_handler,
    login_handler,
    handle_photo,
    handle_document,
    handle_count,
    WAITING_FOR_COUNT,
)
from ..container import get_container
from ..infrastructure.logging import get_logger

logger = get_logger(__name__)


def create_bot_application() -> Application:
    """Bot Application'ı oluştur ve yapılandır"""
    
    container = get_container()
    
    # Application oluştur
    application = Application.builder().token(container.config.bot_token).build()
    
    # DI: Container'ı bot_data'ya enjekte et
    application.bot_data['container'] = container
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.PHOTO, handle_photo),
            MessageHandler(filters.Document.IMAGE, handle_document),
        ],
        states={
            WAITING_FOR_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_count),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
        ],
    )
    
    # Handler'ları ekle
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("login", login_handler))
    application.add_handler(conv_handler)
    
    return application


def run_bot():
    """Bot'u başlat"""
    logger.info("Bot başlatılıyor...")
    
    container = get_container()
    
    # Yapılandırmayı doğrula
    errors = container.config.validate()
    if errors:
        for error in errors:
            logger.error(f"Yapılandırma hatası: {error}")
    
    # Images klasörünü oluştur
    os.makedirs(container.config.images_dir, exist_ok=True)
    
    # Application oluştur ve çalıştır
    application = create_bot_application()
    
    logger.info("Bot çalışıyor! Fotoğraf bekleniyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
