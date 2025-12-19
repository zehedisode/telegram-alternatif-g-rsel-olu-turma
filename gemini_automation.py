"""
Gemini Chrome Otomasyon Modülü
Tam akış: Fotoğraf analizi → Prompt üretimi → Görsel oluşturma → İndirme

Bu modül geriye dönük uyumluluk için korunmuştur.
Yeni kod için 'services.gemini_service.GeminiService' kullanın.
"""

from typing import Optional

import config
from core.logger import get_logger
from core.browser import BrowserManager
from core.clipboard import copy_image_to_clipboard
from core.exceptions import (
    AutomationError,
    BrowserError,
    GeminiError,
)
from services.gemini_service import GeminiService

logger = get_logger(__name__)

# Geriye dönük uyumluluk: copy_image_to_clipboard export
__all__ = ['GeminiAutomation', 'copy_image_to_clipboard']


class GeminiAutomation:
    """
    Gemini otomasyon sınıfı.
    Geriye dönük uyumluluk için API korunmuştur.
    """
    
    def __init__(self):
        self.browser_manager = BrowserManager(
            profile_path=config.CHROME_PROFILE_PATH,
            download_dir=config.IMAGES_DIR
        )
        self.gemini_service: Optional[GeminiService] = None
        self.prompt_text = config.get_prompt_text()
    
    @property
    def driver(self):
        """WebDriver'a erişim (geriye uyumluluk)"""
        return self.browser_manager.driver
    
    def _load_prompt(self) -> str:
        """Prompt dosyasını yükle"""
        return config.get_prompt_text()
    
    def start_browser(self) -> bool:
        """Chrome'u başlat"""
        try:
            self.browser_manager.start()
            self.gemini_service = GeminiService(
                driver=self.browser_manager.driver,
                gemini_url=config.GEMINI_URL,
                download_dir=config.IMAGES_DIR
            )
            return True
        except BrowserError as e:
            logger.error(f"Tarayıcı başlatılamadı: {e}")
            return False
    
    def go_to_gemini(self) -> bool:
        """Gemini sayfasına git"""
        try:
            if self.gemini_service:
                return self.gemini_service.go_to_gemini()
            return False
        except GeminiError as e:
            logger.error(str(e))
            return False
    
    def start_new_chat(self) -> bool:
        """Yeni sohbet başlat"""
        try:
            if self.gemini_service:
                return self.gemini_service.start_new_chat()
            return False
        except GeminiError as e:
            logger.error(str(e))
            return False
    
    def upload_image_clipboard(self, image_path: str) -> bool:
        """Fotoğrafı clipboard ile yükle"""
        try:
            if self.gemini_service:
                return self.gemini_service.upload_image(image_path)
            return False
        except AutomationError as e:
            logger.error(str(e))
            return False
    
    def send_prompt_js(self, prompt_text: str) -> bool:
        """Prompt gönder"""
        try:
            if self.gemini_service:
                return self.gemini_service.send_prompt(prompt_text)
            return False
        except GeminiError as e:
            logger.error(str(e))
            return False
    
    def wait_for_response(self, timeout: int = 120) -> bool:
        """Cevabı bekle"""
        try:
            if self.gemini_service:
                return self.gemini_service.wait_for_response(timeout)
            return False
        except GeminiError as e:
            logger.error(str(e))
            return False
    
    def get_response_text(self) -> Optional[str]:
        """Son cevabı al"""
        try:
            if self.gemini_service:
                return self.gemini_service.get_response_text()
            return None
        except GeminiError as e:
            logger.error(str(e))
            return None
    
    def copy_response(self) -> bool:
        """Cevabı kopyala (eski metod, artık kullanılmıyor)"""
        logger.warning("copy_response() deprecated, get_response_text() kullanın")
        return self.get_response_text() is not None
    
    def wait_for_image_generation(self, timeout: int = 180) -> bool:
        """Görsel oluşturulmasını bekle"""
        try:
            if self.gemini_service:
                return self.gemini_service.wait_for_image_generation(timeout)
            return False
        except GeminiError as e:
            logger.error(str(e))
            return False
    
    def download_generated_image(self) -> Optional[str]:
        """Görseli indir"""
        try:
            if self.gemini_service:
                return self.gemini_service.download_generated_image()
            return None
        except AutomationError as e:
            logger.error(str(e))
            return None
    
    def full_workflow(self, image_path: str) -> Optional[str]:
        """
        Tam akış:
        1. Fotoğraf + prompt gönder
        2. Cevabı bekle ve al
        3. Yeni sohbet aç
        4. Görsel oluşturma promptunu gönder
        5. Görseli indir
        """
        # Tarayıcı kontrolü
        if not self.driver:
            if not self.start_browser():
                return None
        
        try:
            if self.gemini_service:
                return self.gemini_service.full_workflow(
                    image_path=image_path,
                    prompt_text=self.prompt_text
                )
            return None
        except AutomationError as e:
            logger.error(f"Tam akış hatası: {e}")
            return None
    
    def close(self):
        """Tarayıcıyı kapat"""
        self.browser_manager.close()
        self.gemini_service = None


# Test için
if __name__ == "__main__":
    automation = GeminiAutomation()
    print("Gemini otomasyon modülü hazır!")
    print("Tam akış için: automation.full_workflow('/path/to/image.jpg')")
