"""
Telegram Bot Modülü
Kullanıcıdan gelen fotoğrafları dinler, Gemini ile işler ve sonucu geri gönderir.
"""

import os
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
from core.logger import get_logger
from core.browser import BrowserManager
from core.exceptions import AutomationError
from services.gemini_service import GeminiService

logger = get_logger(__name__)


class TelegramBotService:
    """Telegram bot servisi"""
    
    def __init__(self):
        self.browser_manager: Optional[BrowserManager] = None
        self.gemini_service: Optional[GeminiService] = None
        self.prompt_text = config.get_prompt_text()
    
    def ensure_browser(self) -> bool:
        """Tarayıcının çalıştığından emin ol"""
        if self.browser_manager and self.browser_manager.is_running:
            return True
        
        try:
            self.browser_manager = BrowserManager(
                profile_path=config.CHROME_PROFILE_PATH,
                download_dir=config.IMAGES_DIR
            )
            self.browser_manager.start()
            
            self.gemini_service = GeminiService(
                driver=self.browser_manager.driver,
                gemini_url=config.GEMINI_URL,
                download_dir=config.IMAGES_DIR
            )
            return True
            
        except AutomationError as e:
            logger.error(f"Tarayıcı başlatılamadı: {e}")
            return False
    
    def process_image(self, image_path: str) -> Optional[str]:
        """Fotoğrafı işle ve sonuç görselini döndür"""
        if not self.ensure_browser():
            return None
        
        try:
            return self.gemini_service.full_workflow(
                image_path=image_path,
                prompt_text=self.prompt_text
            )
        except AutomationError as e:
            logger.error(f"İşlem hatası: {e}")
            return None
    
    @property
    def browser_status(self) -> str:
        """Tarayıcı durumu"""
        if self.browser_manager and self.browser_manager.is_running:
            return "✅ Aktif"
        return "❌ Kapalı"


# Global servis instance
bot_service = TelegramBotService()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıç komutu"""
    await update.message.reply_text(
        "🤖 Merhaba! Ben AI Görüntü Otomasyon Botuyum.\n\n"
        "📸 Bana bir fotoğraf gönder, ben:\n"
        "1. Gemini'ye yükleyip AI prompt oluşturacağım\n"
        "2. O promptla yeni bir görsel oluşturacağım\n"
        "3. Sonucu sana göndereceğım\n\n"
        "Komutlar:\n"
        "/start - Bu mesajı göster\n"
        "/status - Bot durumunu kontrol et"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durumunu kontrol et"""
    await update.message.reply_text(
        f"📊 Bot Durumu:\n"
        f"🌐 Tarayıcı: {bot_service.browser_status}\n"
        f"📁 Fotoğraf Klasörü: {config.IMAGES_DIR}"
    )


async def process_input_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_obj,
    file_name: str
):
    """Ortak işlem fonksiyonu: fotoğraf ve belge için"""
    status_msg = await update.message.reply_text("📥 Dosya alınıyor...")
    
    try:
        # Dosyayı indir
        file_path = os.path.join(config.IMAGES_DIR, file_name)
        await file_obj.download_to_drive(file_path)
        logger.info(f"Fotoğraf kaydedildi: {file_path}")
        
        await status_msg.edit_text("✅ İndirildi. Chrome kontrol ediliyor...")
        
        await status_msg.edit_text(
            "🔄 Gemini İŞLEMİ BAŞLATILIYOR...\n"
            "1. Fotoğraf Analizi\n"
            "2. Prompt Üretimi\n"
            "3. Görsel Oluşturma"
        )
        
        # Tam akışı çalıştır
        result_image = bot_service.process_image(file_path)
        
        if result_image and os.path.exists(result_image):
            await status_msg.edit_text("✅ Görsel oluşturuldu! Yükleniyor...")
            
            # Dosya olarak gönder (kalite bozulmaz)
            with open(result_image, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(result_image),
                    caption="🎨 İşte sonucunuz!"
                )
            
            # Önizleme gönder
            with open(result_image, 'rb') as f:
                await update.message.reply_photo(photo=f)
            
            await status_msg.edit_text("✅ İşlem başarıyla tamamlandı.")
        else:
            await status_msg.edit_text(
                "❌ Üzgünüm, görsel oluşturulamadı.\n"
                "Olası sebepler:\n"
                "- Gemini görseli oluşturamadı\n"
                "- İndirme zaman aşımına uğradı\n"
                "- İçerik politikası engeli"
            )
    
    except Exception as e:
        logger.error(f"Hata: {e}")
        await status_msg.edit_text(f"❌ Beklenmeyen bir hata oluştu:\n{str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Normal fotoğraf mesajlarını karşılar"""
    logger.info("Fotoğraf alındı.")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    filename = f"photo_{update.message.message_id}.jpg"
    
    await process_input_image(update, context, file, filename)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya olarak gönderilen fotoğrafları karşılar"""
    doc = update.message.document
    
    # MIME type kontrolü
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("⚠️ Lütfen sadece görüntü dosyası gönderin.")
        return
    
    logger.info("Doküman alındı.")
    file = await context.bot.get_file(doc.file_id)
    filename = doc.file_name or f"doc_{update.message.message_id}.jpg"
    
    await process_input_image(update, context, file, filename)


def run_bot():
    """Bot'u başlat"""
    logger.info("Bot başlatılıyor...")
    
    # Yapılandırmayı doğrula
    errors = config.validate_config()
    if errors:
        for error in errors:
            logger.error(f"Yapılandırma hatası: {error}")
    
    # Images klasörünü oluştur
    os.makedirs(config.IMAGES_DIR, exist_ok=True)
    
    # Application oluştur
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Handler'ları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Bot'u çalıştır
    logger.info("Bot çalışıyor! Fotoğraf bekleniyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
