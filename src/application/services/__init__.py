"""
Application Services
İş mantığı servisleri
"""

from typing import Optional
import time
import logging

from ...domain import ProcessStatus, IProgressNotifier

logger = logging.getLogger(__name__)


class ProgressNotifierService(IProgressNotifier):
    """
    İlerleme bildirimi servisi.
    Telegram mesajlarını güncellemek için kullanılır.
    """
    
    # Adım bilgileri
    STEPS = [
        {"status": ProcessStatus.DOWNLOADING, "emoji": "📥", "name": "Dosya indiriliyor"},
        {"status": ProcessStatus.BROWSER_STARTING, "emoji": "🌐", "name": "Chrome başlatılıyor"},
        {"status": ProcessStatus.NAVIGATING, "emoji": "🔗", "name": "Gemini'ye bağlanılıyor"},
        {"status": ProcessStatus.UPLOADING, "emoji": "📤", "name": "Fotoğraf yükleniyor"},
        {"status": ProcessStatus.ANALYZING, "emoji": "🧠", "name": "AI analiz yapıyor"},
        {"status": ProcessStatus.WAITING_RESPONSE, "emoji": "⏳", "name": "Yanıt bekleniyor"},
        {"status": ProcessStatus.PROMPT_RECEIVED, "emoji": "💬", "name": "Prompt alındı"},
        {"status": ProcessStatus.GENERATING, "emoji": "🎨", "name": "Görsel oluşturuluyor"},
        {"status": ProcessStatus.DOWNLOADING_RESULT, "emoji": "📥", "name": "Görsel indiriliyor"},
    ]
    
    def __init__(
        self,
        update_callback,  # async def callback(text: str) -> None
        total_images: int = 1,
    ):
        self.update_callback = update_callback
        self.total_images = total_images
        self.current_image = 0
        self.completed_images = 0
        self.current_step = 0
        self.start_time = time.time()
        self.extra_info = ""
        self._last_update = 0
        self._min_update_interval = 1.5  # Minimum 1.5 saniye ara
        self._is_completed = False  # Tamamlandı flag'i
    
    def _get_step_index(self, status: ProcessStatus) -> int:
        """Status'tan step index bul"""
        for i, step in enumerate(self.STEPS):
            if step["status"] == status:
                return i
        return self.current_step
    
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
                lines.append(f"✅ ~~{step['name']}~~")
            elif i == self.current_step:
                lines.append(f"▶️ **{step['name']}...**")
            else:
                lines.append(f"⬜ {step['name']}")
        
        if self.extra_info:
            lines.append("")
            lines.append(f"💡 _{self.extra_info}_")
        
        elapsed = int(time.time() - self.start_time)
        lines.append("")
        lines.append(f"⏱️ Geçen süre: {elapsed}s")
        
        return "\n".join(lines)
    
    async def notify_step(self, status: ProcessStatus, extra_info: str = "") -> None:
        """Adımı bildir - rate limiting ile"""
        # Tamamlandıysa güncelleme yapma
        if self._is_completed:
            return
        
        self.current_step = self._get_step_index(status)
        self.extra_info = extra_info
        
        # Rate limiting kontrolü
        current_time = time.time()
        if current_time - self._last_update < self._min_update_interval:
            return
        self._last_update = current_time
        
        try:
            await self.update_callback(self._build_message())
        except Exception as e:
            logger.debug(f"Mesaj güncellenemedi: {e}")
    
    async def notify_image_progress(self, current: int, total: int) -> None:
        """Görsel üretim ilerlemesini bildir - rate limiting ile"""
        # Tamamlandıysa güncelleme yapma
        if self._is_completed:
            return
        
        self.current_image = current
        self.total_images = total
        self.completed_images = current  # Tamamlanan sayısını güncelle
        
        # Rate limiting kontrolü
        current_time = time.time()
        if current_time - self._last_update < self._min_update_interval:
            return
        self._last_update = current_time
        
        try:
            await self.update_callback(self._build_message())
        except Exception as e:
            logger.debug(f"Mesaj güncellenemedi: {e}")
    
    async def notify_complete(self, success: bool, details: str = "") -> None:
        """Tamamlanma durumunu bildir - sadece bir kez çağrılır"""
        # Zaten tamamlandıysa tekrar çağırma
        if self._is_completed:
            return
        self._is_completed = True
        
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
            await self.update_callback(text)
        except Exception as e:
            logger.debug(f"Tamamlama mesajı güncellenemedi: {e}")
