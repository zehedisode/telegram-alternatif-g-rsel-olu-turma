"""
Gemini AI Provider
Mevcut GeminiAIService'i OCP uyumlu provider adapter olarak implement eder.
"""

import logging
from typing import Optional
from pathlib import Path

from selenium import webdriver

from .base import BaseAIProvider, AIProviderMeta
from ....core import Result
from ....domain import (
    ImageEntity,
    AIServiceError,
    IBrowserService,
)
from ..gemini import (
    GeminiNavigator,
    GeminiImageUploader,
    GeminiPromptManager,
    GeminiImageGenerator,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Gemini AI Provider - OCP Uyumlu Adapter.
    
    Mevcut Gemini altyapısını BaseAIProvider interface'i ile sarar.
    Result pattern ile tip güvenli hata yönetimi sağlar.
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
    
    @classmethod
    def get_metadata(cls) -> AIProviderMeta:
        """Gemini provider metadata"""
        return AIProviderMeta(
            name="gemini",
            version="1.0.0",
            description="Google Gemini AI görsel analiz ve oluşturma",
            supported_features={"analyze", "generate", "session"},
            priority=10,  # Varsayılan provider
            supports_image_analysis=True,
            supports_image_generation=True,
            max_images_per_request=4,
        )
    
    @property
    def driver(self) -> webdriver.Chrome:
        """WebDriver instance"""
        return self.browser_service.driver
    
    def _ensure_browser(self) -> Result[None, AIServiceError]:
        """Tarayıcının çalıştığından emin ol ve alt modülleri başlat"""
        try:
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
            
            return Result.ok(None)
            
        except Exception as e:
            logger.error(f"Tarayıcı başlatılamadı: {e}")
            return Result.fail(AIServiceError(
                message="Tarayıcı başlatılamadı",
                details=str(e)
            ))
    
    def analyze_image(
        self, 
        image: ImageEntity, 
        prompt: str
    ) -> Result[str, AIServiceError]:
        """
        Görseli analiz et ve prompt döndür.
        Result pattern ile tip güvenli hata yönetimi.
        """
        logger.info(f"Görsel analiz ediliyor: {image.path}")
        
        browser_result = self._ensure_browser()
        if browser_result.is_error:
            return Result.fail(browser_result.error)
        
        try:
            # Alt modüllere delege et
            self._navigator.navigate_to_gemini()
            self._uploader.upload_image(image.path)
            self._prompt_manager.send_prompt(prompt)
            self._prompt_manager.wait_for_response()
            
            response = self._prompt_manager.get_response_text()
            return Result.ok(response)
            
        except Exception as e:
            logger.error(f"Görsel analiz hatası: {e}")
            return Result.fail(AIServiceError(
                message="Görsel analiz başarısız",
                details=str(e)
            ))
    
    def generate_image(
        self, 
        prompt: str
    ) -> Result[ImageEntity, AIServiceError]:
        """
        Prompt kullanarak yeni görsel oluştur.
        Result pattern ile tip güvenli hata yönetimi.
        """
        logger.info(f"Görsel oluşturuluyor: {prompt[:50]}...")
        
        browser_result = self._ensure_browser()
        if browser_result.is_error:
            return Result.fail(browser_result.error)
        
        try:
            # Alt modüllere delege et
            self._image_generator.select_image_generation_tool()
            self._prompt_manager.send_prompt(prompt)
            self._image_generator.wait_for_image_generation()
            
            image = self._image_generator.download_generated_image()
            return Result.ok(image)
            
        except Exception as e:
            logger.error(f"Görsel oluşturma hatası: {e}")
            return Result.fail(AIServiceError(
                message="Görsel oluşturulamadı",
                details=str(e)
            ))
    
    def start_new_session(self) -> Result[None, AIServiceError]:
        """Yeni AI oturumu başlat"""
        logger.info("Yeni sohbet başlatılıyor...")
        
        browser_result = self._ensure_browser()
        if browser_result.is_error:
            return Result.fail(browser_result.error)
        
        try:
            self._navigator.start_new_chat()
            return Result.ok(None)
        except Exception as e:
            logger.error(f"Yeni oturum başlatılamadı: {e}")
            return Result.fail(AIServiceError(
                message="Yeni oturum başlatılamadı",
                details=str(e)
            ))
    
    def cleanup(self) -> None:
        """Kaynakları temizle"""
        if self.browser_service.is_running():
            try:
                self.browser_service.stop()
            except Exception as e:
                logger.warning(f"Tarayıcı kapatılırken hata: {e}")
