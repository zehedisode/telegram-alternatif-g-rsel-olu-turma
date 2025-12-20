"""
Telegram Bot Modülü
Kullanıcıdan gelen fotoğrafları dinler, Gemini ile işler ve sonucu geri gönderir.
Modern ve detaylı adım adım geri bildirimler sağlar.
Çoklu görsel oluşturma desteği.
"""

import os
import time
from typing import Optional
from dataclasses import dataclass

from telegram import Update, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

import config
from core.logger import get_logger
from core.browser import BrowserManager
from core.exceptions import AutomationError
from services.gemini_service import GeminiService

logger = get_logger(__name__)

# Conversation states
WAITING_FOR_COUNT = 1


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
    ]
    
    def __init__(self, message: Message, total_images: int = 1):
        self.message = message
        self.current_step = 0
        self.start_time = time.time()
        self.extra_info = ""
        self.total_images = total_images
        self.current_image = 0
        self.completed_images = 0
    
    def _build_message(self) -> str:
        """İlerleme mesajını oluştur"""
        lines = ["🤖 **AI Görsel Otomasyon**", "━" * 24]
        
        # Çoklu görsel bilgisi
        if self.total_images > 1:
            lines.append(f"🎯 Hedef: **{self.total_images} görsel**")
            if self.current_image > 0:
                lines.append(f"📸 İşleniyor: Görsel {self.current_image}/{self.total_images}")
            if self.completed_images > 0:
                lines.append(f"✅ Tamamlanan: {self.completed_images}/{self.total_images}")
            lines.append("")
        
        for i, step in enumerate(self.STEPS):
            if i < self.current_step:
                lines.append(f"{step.done_emoji} ~~{step.name}~~")
            elif i == self.current_step:
                lines.append(f"▶️ **{step.name}...**")
            else:
                lines.append(f"⬜ {step.name}")
        
        # Görsel oluşturma adımları (prompt alındıktan sonra)
        if self.current_step >= 7 and self.current_image > 0:
            lines.append("")
            lines.append(f"🎨 **Görsel {self.current_image} oluşturuluyor...**")
        
        if self.extra_info:
            lines.append("")
            lines.append(f"💡 _{self.extra_info}_")
        
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
    
    async def set_current_image(self, num: int):
        """Şu anki görsel numarasını ayarla"""
        self.current_image = num
        await self.update(7, f"Görsel {num}/{self.total_images} için yeni sohbet açılıyor...")
    
    async def image_completed(self):
        """Bir görsel tamamlandı"""
        self.completed_images += 1
        await self.update(7, f"{self.completed_images}/{self.total_images} görsel hazır!")
    
    async def complete(self, success: bool, details: str = ""):
        """İşlemi tamamla"""
        elapsed = int(time.time() - self.start_time)
        
        if success:
            if self.total_images > 1:
                text = (
                    f"🎉 **{self.total_images} GÖRSEL OLUŞTURULDU!**\n"
                    "━" * 24 + "\n\n"
                    f"✅ Tüm görseller başarıyla oluşturuldu\n\n"
                    f"⏱️ Toplam süre: **{elapsed} saniye**\n"
                    f"⚡ Ortalama: **{elapsed // self.total_images}s/görsel**\n\n"
                    "📎 Görselleriniz aşağıda 👇"
                )
            else:
                text = (
                    "🎉 **İŞLEM TAMAMLANDI!**\n"
                    "━" * 24 + "\n\n"
                    "✅ Görsel başarıyla oluşturuldu\n\n"
                    f"⏱️ Toplam süre: **{elapsed} saniye**\n\n"
                    "📎 Görseliniz aşağıda 👇"
                )
        else:
            completed_info = ""
            if self.completed_images > 0:
                completed_info = f"\n✅ {self.completed_images} görsel başarıyla oluşturuldu\n"
            
            text = (
                "❌ **İŞLEM BAŞARISIZ**\n"
                "━" * 24 + "\n\n"
                f"⚠️ {details}\n"
                f"{completed_info}\n"
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
    
    async def analyze_image_and_get_prompt(
        self,
        image_path: str,
        progress: ProgressTracker
    ) -> Optional[str]:
        """Fotoğrafı analiz et ve prompt al"""
        
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
            
            return response_text
            
        except AutomationError as e:
            logger.error(f"Analiz hatası: {e}")
            return None
    
    async def generate_single_image(
        self,
        prompt: str,
        image_num: int,
        progress: ProgressTracker
    ) -> Optional[str]:
        """Tek bir görsel oluştur"""
        
        try:
            await progress.set_current_image(image_num)
            
            # Yeni sohbet
            self.gemini_service.start_new_chat()
            
            # Görüntü oluşturma aracını seç
            await progress.update(7, f"Görsel {image_num}: Araç seçiliyor...")
            self.gemini_service.select_image_generation_tool()
            
            # Görsel oluştur
            await progress.update(7, f"Görsel {image_num}: Prompt gönderiliyor...")
            self.gemini_service.send_prompt(prompt)
            
            # Görsel bekle
            await progress.update(7, f"Görsel {image_num}: AI oluşturuyor...")
            self.gemini_service.wait_for_image_generation(timeout=180)
            
            # İndir
            await progress.update(7, f"Görsel {image_num}: İndiriliyor...")
            result = self.gemini_service.download_generated_image()
            
            if result:
                await progress.image_completed()
            
            return result
            
        except AutomationError as e:
            logger.error(f"Görsel {image_num} oluşturma hatası: {e}")
            return None
    
    async def process_image_with_progress(
        self,
        image_path: str,
        image_count: int,
        progress: ProgressTracker
    ) -> tuple:
        """Fotoğrafı işle ve birden fazla görsel oluştur
        
        Returns:
            (results, prompt) - Oluşturulan görsellerin yolları ve kullanılan prompt
        """
        
        results = []
        
        # Önce prompt'u al
        prompt = await self.analyze_image_and_get_prompt(image_path, progress)
        
        if not prompt:
            return results, None
        
        logger.info(f"Prompt alındı, {image_count} görsel oluşturulacak")
        
        # Her görsel için ayrı ayrı oluştur
        for i in range(1, image_count + 1):
            result = await self.generate_single_image(prompt, i, progress)
            if result:
                results.append(result)
        
        return results, prompt
    
    @property
    def browser_status(self) -> str:
        """Tarayıcı durumu"""
        if self.browser_manager and self.browser_manager.is_running:
            return "✅ Aktif"
        return "❌ Kapalı"
    
    def close_browser(self):
        """Tarayıcıyı kapat"""
        if self.browser_manager:
            try:
                self.browser_manager.close()
                logger.info("Tarayıcı kapatıldı")
            except Exception as e:
                logger.warning(f"Tarayıcı kapatılırken hata: {e}")
            finally:
                self.browser_manager = None
                self.gemini_service = None


# Global servis instance
bot_service = TelegramBotService()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıç komutu"""
    welcome_text = """
🤖 **AI Görüntü Otomasyon Botu**
━━━━━━━━━━━━━━━━━━━━━━

📸 **Nasıl Çalışır?**
1️⃣ Bana bir fotoğraf gönder
2️⃣ Kaç adet görsel istediğini belirt (1-9)
3️⃣ AI fotoğrafı analiz eder
4️⃣ İstediğin sayıda görsel üretir
5️⃣ Hepsini sana gönderir

⚡ **Komutlar:**
/start - Bu mesajı göster
/status - Bot durumunu kontrol et
/cancel - İşlemi iptal et

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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """İşlemi iptal et"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ İşlem iptal edildi.\n\n"
        "🔄 Yeni bir fotoğraf göndererek tekrar başlayabilirsiniz.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fotoğraf alındığında sayı sor"""
    logger.info("Fotoğraf alındı, sayı bekleniyor...")
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    filename = f"photo_{update.message.message_id}.jpg"
    
    # Dosyayı kaydet
    file_path = os.path.join(config.IMAGES_DIR, filename)
    await file.download_to_drive(file_path)
    
    # Kullanıcı verisine kaydet
    context.user_data['image_path'] = file_path
    context.user_data['filename'] = filename
    
    await update.message.reply_text(
        "📸 **Fotoğraf alındı!**\n\n"
        "🔢 Kaç adet görsel oluşturmak istiyorsunuz?\n\n"
        "_(1-9 arası bir sayı girin)_\n\n"
        "💡 Örnek: `3` yazarsanız 3 farklı görsel oluşturulur",
        parse_mode="Markdown"
    )
    
    return WAITING_FOR_COUNT


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
    
    file = await context.bot.get_file(doc.file_id)
    filename = doc.file_name or f"doc_{update.message.message_id}.jpg"
    
    # Dosyayı kaydet
    file_path = os.path.join(config.IMAGES_DIR, filename)
    await file.download_to_drive(file_path)
    
    # Kullanıcı verisine kaydet
    context.user_data['image_path'] = file_path
    context.user_data['filename'] = filename
    
    await update.message.reply_text(
        "📸 **Fotoğraf alındı!**\n\n"
        "🔢 Kaç adet görsel oluşturmak istiyorsunuz?\n\n"
        "_(1-9 arası bir sayı girin)_\n\n"
        "💡 Örnek: `3` yazarsanız 3 farklı görsel oluşturulur",
        parse_mode="Markdown"
    )
    
    return WAITING_FOR_COUNT


async def handle_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Görsel sayısını al ve işlemi başlat"""
    text = update.message.text.strip()
    
    # Sayı kontrolü
    try:
        count = int(text)
        if count < 1 or count > 9:
            raise ValueError("Geçersiz aralık")
    except ValueError:
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
    
    # İlerleme takipçisi başlat
    status_msg = await update.message.reply_text(
        "🔄 **Hazırlanıyor...**",
        parse_mode="Markdown"
    )
    progress = ProgressTracker(status_msg, total_images=count)
    
    try:
        await progress.update(0, "Başlatılıyor...")
        
        # İşlemi başlat
        results, used_prompt = await bot_service.process_image_with_progress(
            image_path, count, progress
        )
        
        if results:
            await progress.complete(success=True)
            
            # Her görseli gönder
            for i, result_path in enumerate(results, 1):
                if os.path.exists(result_path):
                    with open(result_path, 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            filename=os.path.basename(result_path),
                            caption=f"🎨 **Görsel {i}/{len(results)}**",
                            parse_mode="Markdown"
                        )
                    
                    with open(result_path, 'rb') as f:
                        await update.message.reply_photo(
                            photo=f,
                            caption=f"👆 _Önizleme {i}/{len(results)}_",
                            parse_mode="Markdown"
                        )
            
            # Kullanılan prompt'u gönder
            if used_prompt:
                # Prompt çok uzunsa kısalt
                prompt_display = used_prompt[:3500] if len(used_prompt) > 3500 else used_prompt
                await update.message.reply_text(
                    f"📝 **Kullanılan Prompt:**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"`{prompt_display}`",
                    parse_mode="Markdown"
                )
        else:
            await progress.complete(
                success=False,
                details="Görsel oluşturulamadı"
            )
    
    except Exception as e:
        logger.error(f"Hata: {e}")
        await progress.complete(success=False, details=str(e))
    
    # Temizlik
    context.user_data.clear()
    
    # Tarayıcıyı kapat
    bot_service.close_browser()
    
    return ConversationHandler.END


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
            CommandHandler("cancel", cancel),
        ],
    )
    
    # Handler'ları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(conv_handler)
    
    # Bot'u çalıştır
    logger.info("Bot çalışıyor! Fotoğraf bekleniyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
