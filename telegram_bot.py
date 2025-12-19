"""
Telegram Bot Modülü
Kullanıcıdan gelen fotoğrafları dinler, Gemini ile işler ve sonucu geri gönderir.
Modern ve detaylı adım adım geri bildirimler sağlar.
"""

import os
import time
from typing import Optional, Callable
from dataclasses import dataclass

from telegram import Update, Message
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


@dataclass
class StepInfo:
    """İşlem adımı bilgisi"""
    emoji: str
    name: str
    done_emoji: str = "✅"


class ProgressTracker:
    """Modern ilerleme takipçisi"""
    
    STEPS = [
        StepInfo("📥", "Dosya indiriliyor"),
        StepInfo("🌐", "Chrome başlatılıyor"),
        StepInfo("🔗", "Gemini'ye bağlanılıyor"),
        StepInfo("📤", "Fotoğraf yükleniyor"),
        StepInfo("🧠", "AI analiz yapıyor"),
        StepInfo("⏳", "Yanıt bekleniyor"),
        StepInfo("💬", "Prompt alındı"),
        StepInfo("🆕", "Yeni sohbet açılıyor"),
        StepInfo("🎨", "Görsel oluşturuluyor"),
        StepInfo("⬇️", "Görsel indiriliyor"),
        StepInfo("📨", "Sonuç gönderiliyor"),
    ]
    
    def __init__(self, message: Message):
        self.message = message
        self.current_step = 0
        self.start_time = time.time()
        self.extra_info = ""
    
    def _build_message(self) -> str:
        """İlerleme mesajını oluştur"""
        lines = ["🤖 **AI Görsel Otomasyon**", "━" * 24, ""]
        
        for i, step in enumerate(self.STEPS):
            if i < self.current_step:
                # Tamamlanmış adım
                lines.append(f"{step.done_emoji} ~~{step.name}~~")
            elif i == self.current_step:
                # Aktif adım
                lines.append(f"▶️ **{step.name}...**")
            else:
                # Bekleyen adım
                lines.append(f"⬜ {step.name}")
        
        # Ekstra bilgi
        if self.extra_info:
            lines.append("")
            lines.append(f"💡 _{self.extra_info}_")
        
        # Geçen süre
        elapsed = int(time.time() - self.start_time)
        lines.append("")
        lines.append(f"⏱️ Geçen süre: {elapsed}s")
        
        return "\n".join(lines)
    
    async def update(self, step: int, extra_info: str = ""):
        """Adımı güncelle"""
        self.current_step = step
        self.extra_info = extra_info
        
        try:
            await self.message.edit_text(
                self._build_message(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.debug(f"Mesaj güncellenemedi: {e}")
    
    async def complete(self, success: bool, details: str = ""):
        """İşlemi tamamla"""
        elapsed = int(time.time() - self.start_time)
        
        if success:
            text = (
                "🎉 **İŞLEM TAMAMLANDI!**\n"
                "━" * 24 + "\n\n"
                "✅ Tüm adımlar başarıyla tamamlandı\n\n"
                f"⏱️ Toplam süre: **{elapsed} saniye**\n\n"
                "📎 Görseliniz aşağıda 👇"
            )
        else:
            text = (
                "❌ **İŞLEM BAŞARISIZ**\n"
                "━" * 24 + "\n\n"
                f"⚠️ {details}\n\n"
                f"⏱️ Geçen süre: {elapsed}s\n\n"
                "🔄 Tekrar denemek için yeni bir fotoğraf gönderin."
            )
        
        try:
            await self.message.edit_text(text, parse_mode="Markdown")
        except Exception as e:
            logger.debug(f"Tamamlama mesajı güncellenemedi: {e}")


class TelegramBotService:
    """Telegram bot servisi"""
    
    def __init__(self):
        self.browser_manager: Optional[BrowserManager] = None
        self.gemini_service: Optional[GeminiService] = None
        self.prompt_text = config.get_prompt_text()
    
    async def ensure_browser(self, progress: ProgressTracker) -> bool:
        """Tarayıcının çalıştığından emin ol"""
        if self.browser_manager and self.browser_manager.is_running:
            return True
        
        await progress.update(1, "Chrome profili yükleniyor...")
        
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
    
    async def process_image_with_progress(
        self,
        image_path: str,
        progress: ProgressTracker
    ) -> Optional[str]:
        """Fotoğrafı işle ve ilerlemeyi takip et"""
        
        # Tarayıcı kontrolü
        if not await self.ensure_browser(progress):
            return None
        
        try:
            # Adım 2: Gemini'ye bağlan
            await progress.update(2, "Gemini sayfası açılıyor...")
            self.gemini_service.go_to_gemini()
            
            # Adım 3: Fotoğraf yükle
            await progress.update(3, "Fotoğraf clipboard'a kopyalanıyor...")
            self.gemini_service.upload_image(image_path)
            
            # Adım 4: Analiz başlat
            await progress.update(4, "Prompt gönderiliyor...")
            self.gemini_service.send_prompt(self.prompt_text)
            
            # Adım 5: Yanıt bekle
            await progress.update(5, "Gemini düşünüyor...")
            self.gemini_service.wait_for_response(timeout=120)
            
            # Adım 6: Prompt al
            await progress.update(6, "AI prompt alınıyor...")
            response_text = self.gemini_service.get_response_text()
            if not response_text:
                raise AutomationError("Yanıt alınamadı")
            
            # Adım 7: Yeni sohbet
            await progress.update(7, "Görsel oluşturma için hazırlanıyor...")
            self.gemini_service.start_new_chat()
            
            # Adım 8: Görsel oluştur
            await progress.update(8, "Görsel oluşturma promptu gönderiliyor...")
            self.gemini_service.send_prompt(response_text)
            
            # Adım 9: Görsel bekle
            await progress.update(9, "AI görsel oluşturuyor (bu biraz sürebilir)...")
            self.gemini_service.wait_for_image_generation(timeout=180)
            
            # Adım 10: İndir
            await progress.update(9, "Görsel indiriliyor...")
            result = self.gemini_service.download_generated_image()
            
            return result
            
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
    welcome_text = """
🤖 **AI Görüntü Otomasyon Botu**
━━━━━━━━━━━━━━━━━━━━━━

📸 **Nasıl Çalışır?**
1️⃣ Bana bir fotoğraf gönder
2️⃣ AI fotoğrafı analiz eder
3️⃣ Detaylı bir prompt oluşturur
4️⃣ Bu promptla yeni görsel üretir
5️⃣ Sonucu sana gönderir

⚡ **Komutlar:**
/start - Bu mesajı göster
/status - Bot durumunu kontrol et

🎯 Hadi başlayalım! Bir fotoğraf gönder.
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durumunu kontrol et"""
    status_text = f"""
📊 **Bot Durumu**
━━━━━━━━━━━━━━━━

🌐 Tarayıcı: {bot_service.browser_status}
📁 Klasör: `{config.IMAGES_DIR}`
🔗 Gemini: {config.GEMINI_URL}

✅ Bot aktif ve fotoğraf bekliyor!
"""
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def process_input_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_obj,
    file_name: str
):
    """Ortak işlem fonksiyonu: fotoğraf ve belge için"""
    
    # İlerleme takipçisi başlat
    status_msg = await update.message.reply_text(
        "🚀 **İşlem başlatılıyor...**",
        parse_mode="Markdown"
    )
    progress = ProgressTracker(status_msg)
    
    try:
        # Adım 0: Dosyayı indir
        await progress.update(0, "Telegram'dan indiriliyor...")
        file_path = os.path.join(config.IMAGES_DIR, file_name)
        await file_obj.download_to_drive(file_path)
        logger.info(f"Fotoğraf kaydedildi: {file_path}")
        
        # İşlemi başlat
        result_image = await bot_service.process_image_with_progress(
            file_path, progress
        )
        
        if result_image and os.path.exists(result_image):
            # Adım 10: Gönder
            await progress.update(10, "Telegram'a yükleniyor...")
            
            # Tamamlandı mesajı
            await progress.complete(success=True)
            
            # Dosya olarak gönder (kalite bozulmaz)
            with open(result_image, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(result_image),
                    caption="🎨 **Orijinal Kalite**\nTam çözünürlüklü görsel",
                    parse_mode="Markdown"
                )
            
            # Önizleme gönder
            with open(result_image, 'rb') as f:
                await update.message.reply_photo(
                    photo=f,
                    caption="👆 _Önizleme - Orijinal için dosyaya bakın_",
                    parse_mode="Markdown"
                )
        else:
            await progress.complete(
                success=False,
                details="Görsel oluşturulamadı veya indirilemedi"
            )
    
    except Exception as e:
        logger.error(f"Hata: {e}")
        await progress.complete(success=False, details=str(e))


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
        await update.message.reply_text(
            "⚠️ **Hata:** Lütfen sadece görüntü dosyası gönderin.",
            parse_mode="Markdown"
        )
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
