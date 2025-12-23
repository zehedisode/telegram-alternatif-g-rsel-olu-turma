"""
Conversation Handlers
Görsel sayısı alma ve işleme akışı

DI Pattern: Bağımlılıklar context.bot_data üzerinden enjekte edilir.
"""

import os
import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ...domain import ImageEntity, ImageCount, ValidationError
from ...application import ImageProcessRequest, ProgressNotifierService
from .photo_handlers import WAITING_FOR_COUNT

if TYPE_CHECKING:
    from ...container import Container

logger = logging.getLogger(__name__)


def _get_container(context: ContextTypes.DEFAULT_TYPE) -> "Container":
    """
    Context'ten container al.
    DI Pattern: Container bot_data üzerinden enjekte edilir.
    """
    container = context.bot_data.get('container')
    if not container:
        # Fallback - sadece geçiş dönemi için
        from ...container import get_container
        container = get_container()
        context.bot_data['container'] = container
    return container


async def handle_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Görsel sayısını al ve işlemi başlat"""
    text = update.message.text.strip()
    
    # Value Object ile doğrulama
    try:
        image_count = ImageCount.from_string(text)
        count = int(image_count)
    except ValueError as e:
        await update.message.reply_text(
            "⚠️ **Geçersiz sayı!**\n\n"
            "Lütfen 1-9 arası bir sayı girin.\n\n"
            "_Örnek: 1, 3, 5, 9_",
            parse_mode="Markdown"
        )
        return WAITING_FOR_COUNT
    
    # Dosya yolunu al
    image_path = context.user_data.get('image_path')
    if not image_path or not os.path.exists(image_path):
        await update.message.reply_text(
            "❌ **Hata:** Fotoğraf bulunamadı.\n\n"
            "Lütfen tekrar bir fotoğraf gönderin.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Onay mesajı
    await update.message.reply_text(
        f"✅ **{count} görsel** oluşturulacak!\n\n"
        "🚀 İşlem başlatılıyor...",
        parse_mode="Markdown"
    )
    
    # İlerleme mesajı
    status_msg = await update.message.reply_text(
        "🔄 **Hazırlanıyor...**",
        parse_mode="Markdown"
    )
    
    # Progress callback oluştur
    async def update_callback(text: str):
        try:
            await status_msg.edit_text(text, parse_mode="Markdown")
        except Exception as e:
            logger.debug(f"Mesaj güncellenemedi: {e}")
    
    progress_notifier = ProgressNotifierService(
        update_callback=update_callback,
        total_images=count,
    )
    
    try:
        # DI Pattern üzerinden container al
        container = _get_container(context)
        
        # === OTOMATİK OTURUM KONTROLÜ ===
        try:
            is_valid, session_msg = container.ai_service.check_session()
            if not is_valid:
                await update.message.reply_text(
                    "⚠️ **Gemini Oturumu Kapalı!**\n\n"
                    f"📌 Durum: {session_msg}\n\n"
                    "🔐 Lütfen `/login` komutu ile giriş yapın,\n"
                    "ardından tekrar fotoğraf gönderin.",
                    parse_mode="Markdown"
                )
                context.user_data.clear()
                return ConversationHandler.END
        except Exception as e:
            logger.warning(f"Oturum kontrolü atlandı: {e}")
        
        # İşlem isteği oluştur
        request = ImageProcessRequest(
            chat_id=str(update.message.chat_id),
            user_id=str(update.message.from_user.id),
            image_path=image_path,
            target_count=count,
        )
        
        # İş akışını çalıştır
        result = await container.process_workflow_use_case.execute(
            request=request,
            system_prompt=container.config.prompt_text,
            progress_notifier=progress_notifier,
        )
        
        if result.success:
            await progress_notifier.notify_complete(success=True)
            
            # Görselleri gönder
            for i, img_path in enumerate(result.generated_image_paths, 1):
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            filename=os.path.basename(img_path),
                            caption=f"🎨 **Görsel {i}/{len(result.generated_image_paths)}**",
                            parse_mode="Markdown"
                        )
                    
                    with open(img_path, 'rb') as f:
                        await update.message.reply_photo(
                            photo=f,
                            caption=f"👆 _Önizleme {i}/{len(result.generated_image_paths)}_",
                            parse_mode="Markdown"
                        )
            
            # Prompt'u gönder
            if result.extracted_prompt:
                prompt_display = result.extracted_prompt[:3500]
                await update.message.reply_text(
                    f"📝 **Kullanılan Prompt:**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"`{prompt_display}`",
                    parse_mode="Markdown"
                )
        else:
            await progress_notifier.notify_complete(
                success=False,
                details=result.error_message or "Bilinmeyen hata"
            )
    
    except Exception as e:
        logger.error(f"Hata: {e}")
        await progress_notifier.notify_complete(success=False, details=str(e))
    
    # Temizlik
    context.user_data.clear()
    
    return ConversationHandler.END
