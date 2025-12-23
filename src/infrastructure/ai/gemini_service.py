"""
Gemini AI Service - Refactored (Facade Pattern)
Clean Architecture uyumlu Gemini etkileşim servisi.

SRP: Bu sınıf artık sadece alt modülleri orkestre eder.
Alt modüller:
- GeminiNavigator: Sayfa navigasyonu
- GeminiImageUploader: Görsel yükleme
- GeminiPromptManager: Prompt gönderme/yanıt alma
- GeminiImageGenerator: Görsel oluşturma ve indirme
"""

import logging
from typing import Optional, Tuple
from pathlib import Path

from selenium import webdriver

from ...domain import (
    IAIService,
    IBrowserService,
    ImageEntity,
)
from .gemini import (
    GeminiNavigator,
    GeminiImageUploader,
    GeminiPromptManager,
    GeminiImageGenerator,
)

logger = logging.getLogger(__name__)


class GeminiAIService(IAIService):
    """
    Clean Architecture uyumlu Gemini AI Servis implementasyonu.
    Facade Pattern: Alt modülleri orkestre eder.
    """
    
    def __init__(
        self,
        browser_service: IBrowserService,
        gemini_url: str,
        download_dir: str,
    ):
        self.browser_service = browser_service
        self.gemini_url = gemini_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Alt modüller (lazy initialization)
        self._navigator: Optional[GeminiNavigator] = None
        self._uploader: Optional[GeminiImageUploader] = None
        self._prompt_manager: Optional[GeminiPromptManager] = None
        self._image_generator: Optional[GeminiImageGenerator] = None
    
    @property
    def driver(self) -> webdriver.Chrome:
        """WebDriver instance"""
        return self.browser_service.driver
    
    def _ensure_browser(self) -> None:
        """Tarayıcının çalıştığından emin ol ve alt modülleri başlat"""
        if not self.browser_service.is_running():
            self.browser_service.start()
        
        # Alt modülleri lazy olarak başlat
        if not self._navigator:
            self._navigator = GeminiNavigator(self.driver, self.gemini_url)
        if not self._uploader:
            self._uploader = GeminiImageUploader(self.driver)
        if not self._prompt_manager:
            self._prompt_manager = GeminiPromptManager(self.driver)
        if not self._image_generator:
            self._image_generator = GeminiImageGenerator(
                self.driver, 
                str(self.download_dir)
            )
    
    def check_session(self) -> Tuple[bool, str]:
        """
        Gemini oturumunu kontrol et.
        
        Returns:
            (is_valid, message) tuple'ı
        """
        try:
            self._ensure_browser()
            return self._navigator.check_session()
        except Exception as e:
            return False, f"Oturum kontrolü hatası: {str(e)}"
    
    def is_session_valid(self) -> bool:
        """Oturum geçerli mi?"""
        is_valid, _ = self.check_session()
        return is_valid
    
    # === IAIService Interface Implementasyonu ===
    
    def analyze_image(self, image: ImageEntity, prompt: str) -> str:
        """
        Görseli analiz et ve prompt döndür.
        IAIService interface'ini implement eder.
        """
        logger.info(f"Görsel analiz ediliyor: {image.path}")
        
        self._ensure_browser()
        
        # Alt modüllere delege et
        self._navigator.navigate_to_gemini()
        self._uploader.upload_image(image.path)
        self._prompt_manager.send_prompt(prompt)
        self._prompt_manager.wait_for_response()
        
        return self._prompt_manager.get_response_text()
    
    def generate_image(self, prompt: str) -> ImageEntity:
        """
        Prompt kullanarak yeni görsel oluştur.
        IAIService interface'ini implement eder.
        """
        logger.info(f"Görsel oluşturuluyor: {prompt[:50]}...")
        
        self._ensure_browser()
        
        # Alt modüllere delege et
        self._image_generator.select_image_generation_tool()
        self._prompt_manager.send_prompt(prompt)
        self._image_generator.wait_for_image_generation()
        
        return self._image_generator.download_generated_image()
    
    def start_new_session(self) -> None:
        """Yeni AI oturumu başlat"""
        logger.info("Yeni sohbet başlatılıyor...")
        
        self._ensure_browser()
        self._navigator.start_new_chat()

