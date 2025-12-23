"""
Gemini Image Generator
Görsel oluşturma işlemleri.
SRP: Sadece görsel oluşturma sorumluluğu.
"""

import time
import logging
from typing import TYPE_CHECKING, Optional
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ....domain import ImageGenerationError, ImageEntity
from .selectors import GeminiSelectors
from .timeouts import GeminiTimeouts
from ..downloader import ImageDownloaderService

if TYPE_CHECKING:
    from selenium import webdriver

logger = logging.getLogger(__name__)


class GeminiImageGenerator:
    """
    Gemini görsel oluşturma işlemleri.
    Tek Sorumluluk: AI ile görsel oluşturma ve indirme.
    """
    
    def __init__(self, driver: "webdriver.Chrome", download_dir: str):
        self.driver = driver
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.downloader: Optional[ImageDownloaderService] = None
    
    def _ensure_downloader(self) -> None:
        """Downloader'ın hazır olduğundan emin ol"""
        if not self.downloader:
            self.downloader = ImageDownloaderService(
                self.driver, 
                str(self.download_dir)
            )
    
    def select_image_generation_tool(self) -> bool:
        """Araçlar menüsünden görüntü oluşturun seçeneğini seç"""
        logger.info("Görüntü oluşturma aracı seçiliyor...")
        
        try:
            wait = WebDriverWait(self.driver, GeminiTimeouts.BUTTON_CLICK)
            time.sleep(GeminiTimeouts.MEDIUM_WAIT)
            
            # Araçlar butonunu bul
            tools_button = None
            for selector in GeminiSelectors.TOOLS_BUTTON_VARIANTS:
                try:
                    tools_button = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, selector)
                    ))
                    break
                except Exception:
                    continue
            
            if not tools_button:
                logger.error("Araçlar butonu bulunamadı!")
                return False
            
            # Araçlar butonuna tıkla
            self.driver.execute_script("arguments[0].click();", tools_button)
            time.sleep(GeminiTimeouts.MEDIUM_WAIT)
            
            # Seçenekleri bul
            options = []
            for selector in GeminiSelectors.OPTION_SELECTORS:
                options = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if options:
                    break
            
            if not options:
                logger.error("Menü seçenekleri bulunamadı!")
                return False
            
            # Görüntü oluşturun seçeneğini bul
            for option in options:
                option_text = option.text.strip().lower()
                if 'görüntü oluştur' in option_text or 'create image' in option_text:
                    self.driver.execute_script("arguments[0].click();", option)
                    time.sleep(GeminiTimeouts.SHORT_WAIT)
                    logger.info("✓ Görüntü oluşturma aracı seçildi!")
                    return True
            
            # Fallback
            if len(options) > 2:
                self.driver.execute_script("arguments[0].click();", options[2])
                time.sleep(GeminiTimeouts.SHORT_WAIT)
                logger.info("✓ Görüntü oluşturma aracı seçildi (fallback)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Görüntü oluşturma aracı seçilemedi: {e}")
            return False
    
    def wait_for_image_generation(
        self, 
        timeout: int = GeminiTimeouts.IMAGE_GENERATION
    ) -> None:
        """Görsel oluşturulmasını bekle"""
        logger.info("Görsel oluşturulması bekleniyor...")
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, GeminiSelectors.IMAGE_BUTTON)
            ))
            
            time.sleep(GeminiTimeouts.RESPONSE_CHECK)
            logger.info("Görsel oluşturuldu!")
            
        except Exception as e:
            raise ImageGenerationError(
                "Görsel oluşturulamadı veya timeout",
                details=str(e)
            )
    
    def download_generated_image(self) -> ImageEntity:
        """Oluşturulan görseli indir"""
        self._ensure_downloader()
        
        downloaded_path = self.downloader.download()
        
        if not downloaded_path:
            raise ImageGenerationError("Görsel indirilemedi")
        
        return ImageEntity(path=downloaded_path)
