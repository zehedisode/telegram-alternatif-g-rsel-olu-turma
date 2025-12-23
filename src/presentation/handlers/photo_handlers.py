"""
Photo Handlers
Fotoğraf ve doküman işleme handler'ları
DRY prensibi: handle_photo ve handle_document birleştirildi
"""

import os
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_COUNT = 1


async def _save_image_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
    filename: str,
    images_dir: str,
) -> str:
    """
    Görsel dosyasını kaydet - ortak fonksiyon (DRY).
    """
    file = await context.bot.get_file(file_id)
    file_path = os.path.join(images_dir, filename)
    await file.download_to_drive(file_path)
    
    # Kullanıcı verisine kaydet
    context.user_data['image_path'] = file_path
    context.user_data['filename'] = filename
    
    return file_path


async def _ask_for_count(update: Update) -> int:
    """Görsel sayısını sor - ortak mesaj"""
    await update.message.reply_text(
        "📸 **Fotoğraf alındı!**\n\n"
        "🔢 Kaç adet görsel oluşturmak istiyorsunuz?\n\n"
        "_(1-9 arası bir sayı girin)_\n\n"
        "💡 Örnek: `3` yazarsanız 3 farklı görsel oluşturulur",
        parse_mode="Markdown"
    )
    return WAITING_FOR_COUNT


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fotoğraf alındığında sayı sor"""
    logger.info("Fotoğraf alındı, sayı bekleniyor...")
    
    from ...container import get_container
    container = get_container()
    
    photo = update.message.photo[-1]
    filename = f"photo_{update.message.message_id}.jpg"
    
    await _save_image_file(
        update, context,
        file_id=photo.file_id,
        filename=filename,
        images_dir=container.config.images_dir,
    )
    
    return await _ask_for_count(update)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya olarak gönderilen fotoğrafları karşılar"""
    doc = update.message.document
    
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text(
            "⚠️ **Hata:** Lütfen sadece görüntü dosyası gönderin.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    logger.info("Doküman alındı, sayı bekleniyor...")
    
    from ...container import get_container
    container = get_container()
    
    filename = doc.file_name or f"doc_{update.message.message_id}.jpg"
    
    await _save_image_file(
        update, context,
        file_id=doc.file_id,
        filename=filename,
        images_dir=container.config.images_dir,
    )
    
    return await _ask_for_count(update)
