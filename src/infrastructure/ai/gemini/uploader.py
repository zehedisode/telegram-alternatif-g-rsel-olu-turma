"""
Gemini Image Uploader
Görsel yükleme işlemleri.
SRP: Sadece görsel yükleme sorumluluğu.
"""

import time
import logging
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from ....domain import AIServiceError
from .selectors import GeminiSelectors
from .scripts import GeminiScripts
from .timeouts import GeminiTimeouts
from ..clipboard import ClipboardService

if TYPE_CHECKING:
    from selenium import webdriver

logger = logging.getLogger(__name__)


class GeminiImageUploader:
    """
    Gemini görsel yükleme işlemleri.
    Tek Sorumluluk: Görsel yükleme ve doğrulama.
    """
    
    def __init__(self, driver: "webdriver.Chrome"):
        self.driver = driver
        self.clipboard_service = ClipboardService()
    
    def upload_image(self, image_path: str) -> None:
        """Görseli clipboard yöntemiyle yükle"""
        logger.info(f"Fotoğraf yükleniyor: {image_path}")
        
        try:
            wait = WebDriverWait(self.driver, GeminiTimeouts.ELEMENT_VISIBLE)
            
            # Clipboard'a kopyala
            self.clipboard_service.copy_image(image_path)
            time.sleep(GeminiTimeouts.CLIPBOARD_WAIT)
            
            # Prompt alanına tıkla
            prompt_area = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, GeminiSelectors.PROMPT_AREA)
            ))
            prompt_area.click()
            time.sleep(GeminiTimeouts.SHORT_WAIT)
            
            # Ctrl+V ile yapıştır
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            
            logger.info("Fotoğraf yapıştırıldı, yüklenmesi bekleniyor...")
            time.sleep(GeminiTimeouts.IMAGE_UPLOAD)
            
            # Doğrulama
            self._verify_upload()
            
        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError("Fotoğraf yüklenemedi", details=str(e))
    
    def _verify_upload(self) -> bool:
        """Yüklemenin başarılı olduğunu doğrula"""
        for _ in range(GeminiTimeouts.IMAGE_VERIFY):
            try:
                uploaded = self.driver.execute_script(GeminiScripts.CHECK_UPLOADED_IMAGE)
                if uploaded:
                    logger.info("Fotoğraf yüklendi ve doğrulandı!")
                    time.sleep(GeminiTimeouts.MEDIUM_WAIT)
                    return True
            except Exception:
                pass
            time.sleep(GeminiTimeouts.SHORT_WAIT)
        
        logger.warning("Fotoğraf yüklemesi doğrulanamadı, devam ediliyor...")
        return False
