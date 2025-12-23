"""
Command Handlers
/start, /status, /cancel, /login komutları için handler'lar
"""

import logging
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
/login - Gemini oturumu aç
/cancel - İşlemi iptal et

🎯 Hadi başlayalım! Bir fotoğraf gönder.
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durumunu kontrol et"""
    # Container'dan durum almak için import
    from ...container import get_container
    
    try:
        container = get_container()
        browser_status = "✅ Aktif" if container.browser_service.is_running() else "❌ Kapalı"
        images_dir = container.config.images_dir
        gemini_url = container.config.gemini_url
    except Exception as e:
        browser_status = "❌ Hata"
        images_dir = "Bilinmiyor"
        gemini_url = "Bilinmiyor"
        logger.error(f"Status hatası: {e}")
    
    status_text = f"""
📊 **Bot Durumu**
━━━━━━━━━━━━━━━━

🌐 Tarayıcı: {browser_status}
📁 Klasör: `{images_dir}`
🔗 Gemini: {gemini_url}

✅ Bot aktif ve fotoğraf bekliyor!
"""
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gemini oturumu aç.
    Chrome'u başlatır ve Gemini sayfasına gider.
    Kullanıcı manuel olarak giriş yapabilir.
    """
    from ...container import get_container
    
    await update.message.reply_text(
        "🔐 **Gemini Oturumu Açılıyor...**\n\n"
        "⏳ Chrome başlatılıyor, lütfen bekleyin...",
        parse_mode="Markdown"
    )
    
    try:
        container = get_container()
        
        # Tarayıcıyı başlat
        if not container.browser_service.is_running():
            container.browser_service.start()
            await asyncio.sleep(2)
        
        # Gemini'ye git
        gemini_url = container.config.gemini_url
        container.browser_service.navigate_to(gemini_url)
        await asyncio.sleep(3)
        
        # Durum mesajı
        await update.message.reply_text(
            "✅ **Chrome Açıldı!**\n\n"
            "📌 **Yapmanız gereken:**\n"
            "1️⃣ Açılan Chrome penceresine gidin\n"
            "2️⃣ Google hesabınızla giriş yapın\n"
            "3️⃣ Gemini sayfasının yüklendiğinden emin olun\n\n"
            "⚠️ Giriş yaptıktan sonra Chrome'u **kapatmayın**!\n"
            "Bot bu oturumu kullanacak.\n\n"
            "✅ Giriş tamamlandıktan sonra fotoğraf gönderebilirsiniz.",
            parse_mode="Markdown"
        )
        
        logger.info("Gemini login sayfası açıldı")
        
    except Exception as e:
        logger.error(f"Login hatası: {e}")
        await update.message.reply_text(
            f"❌ **Hata!**\n\n"
            f"Chrome açılamadı: `{str(e)}`\n\n"
            f"🔧 Çözüm: Chrome profilinin doğru yolda olduğundan emin olun.",
            parse_mode="Markdown"
        )


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """İşlemi iptal et"""
    from telegram.ext import ConversationHandler
    
    context.user_data.clear()
    await update.message.reply_text(
        "❌ İşlem iptal edildi.\n\n"
        "🔄 Yeni bir fotoğraf göndererek tekrar başlayabilirsiniz.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

