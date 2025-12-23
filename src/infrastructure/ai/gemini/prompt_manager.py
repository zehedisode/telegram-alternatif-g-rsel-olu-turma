"""
Gemini Prompt Manager
Prompt gönderme ve yanıt alma işlemleri.
SRP: Sadece metin etkileşimi sorumluluğu.
"""

import time
import logging
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ....domain import AIServiceError, ResponseError
from .selectors import GeminiSelectors
from .scripts import GeminiScripts
from .timeouts import GeminiTimeouts

if TYPE_CHECKING:
    from selenium import webdriver

logger = logging.getLogger(__name__)


class GeminiPromptManager:
    """
    Gemini prompt gönderme ve yanıt alma.
    Tek Sorumluluk: Metin tabanlı etkileşim.
    """
    
    def __init__(self, driver: "webdriver.Chrome"):
        self.driver = driver
    
    def send_prompt(self, prompt_text: str) -> None:
        """Prompt gönder"""
        logger.info("Prompt gönderiliyor...")
        
        try:
            wait = WebDriverWait(self.driver, GeminiTimeouts.ELEMENT_CLICKABLE)
            time.sleep(GeminiTimeouts.SHORT_WAIT)
            
            # JavaScript ile prompt yaz
            self.driver.execute_script(GeminiScripts.WRITE_PROMPT, prompt_text)
            time.sleep(GeminiTimeouts.MEDIUM_WAIT)
            
            # Gönder butonuna tıkla
            send_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, GeminiSelectors.SEND_BUTTON)
            ))
            self.driver.execute_script("arguments[0].click();", send_button)
            
            logger.info("Prompt gönderildi!")
            
        except Exception as e:
            raise AIServiceError("Prompt gönderilemedi", details=str(e))
    
    def wait_for_response(self, timeout: int = GeminiTimeouts.RESPONSE_WAIT) -> None:
        """Cevabı bekle"""
        logger.info("Cevap bekleniyor...")
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            time.sleep(GeminiTimeouts.LONG_WAIT)
            
            # Stop butonunun kaybolmasını bekle
            try:
                wait.until_not(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, GeminiSelectors.STOP_BUTTON)
                ))
            except Exception:
                pass
            
            time.sleep(GeminiTimeouts.RESPONSE_CHECK)
            logger.info("Cevap alındı!")
            
        except Exception as e:
            raise ResponseError("Cevap beklenirken hata", details=str(e))
    
    def get_response_text(self) -> str:
        """Son cevabı al - birden fazla selector dener"""
        logger.info("Cevap metni alınıyor...")
        
        # Önce tag name olarak dene
        try:
            responses = self.driver.find_elements(By.TAG_NAME, 'model-response')
            if responses:
                text_content = self.driver.execute_script(
                    GeminiScripts.GET_RESPONSE_TEXT, 
                    responses[-1]
                )
                if text_content and len(text_content.strip()) > 10:
                    logger.info(f"Cevap alındı (tag): {text_content[:100]}...")
                    return text_content.strip()
        except Exception as e:
            logger.debug(f"Tag name ile yanıt alınamadı: {e}")
        
        # CSS selector varyantlarını dene
        for selector in GeminiSelectors.MODEL_RESPONSE_VARIANTS:
            try:
                # Tag name ise farklı selector kullan
                if selector == 'model-response':
                    continue  # Yukarıda denendi
                
                responses = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if responses:
                    text_content = self.driver.execute_script(
                        GeminiScripts.GET_RESPONSE_TEXT, 
                        responses[-1]
                    )
                    if text_content and len(text_content.strip()) > 10:
                        logger.info(f"Cevap alındı ({selector}): {text_content[:100]}...")
                        return text_content.strip()
            except Exception as e:
                logger.debug(f"Selector {selector} ile yanıt alınamadı: {e}")
                continue
        
        raise ResponseError("Yanıt bulunamadı - Gemini oturumunu kontrol edin")

