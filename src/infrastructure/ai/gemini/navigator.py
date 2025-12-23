"""
Gemini Navigator
Sayfa navigasyonu ve temel bekleme işlemleri.
SRP: Sadece navigasyon sorumluluğu.
"""

import time
import logging
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ....domain import NavigationError
from .selectors import GeminiSelectors
from .timeouts import GeminiTimeouts

if TYPE_CHECKING:
    from selenium import webdriver

logger = logging.getLogger(__name__)


class GeminiNavigator:
    """
    Gemini sayfa navigasyonu.
    Tek Sorumluluk: Sayfa yükleme ve navigasyon.
    """
    
    def __init__(self, driver: "webdriver.Chrome", gemini_url: str):
        self.driver = driver
        self.gemini_url = gemini_url
    
    def navigate_to_gemini(self) -> None:
        """Gemini sayfasına git"""
        logger.info("Gemini'ye gidiliyor...")
        
        try:
            self.driver.get(self.gemini_url)
            time.sleep(GeminiTimeouts.PAGE_LOAD)
            logger.info("Gemini sayfası açıldı")
        except Exception as e:
            raise NavigationError("Gemini'ye gidilemedi", details=str(e))
    
    def is_logged_in(self) -> bool:
        """
        Gemini oturumunun açık olup olmadığını kontrol et.
        
        Returns:
            True eğer kullanıcı giriş yapmışsa
        """
        try:
            # Prompt alanı varsa giriş yapılmış demektir
            prompt_selectors = [
                'div[role="textbox"]',
                '.ql-editor',
                'rich-textarea',
                '[contenteditable="true"]',
            ]
            
            for selector in prompt_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.debug(f"Login kontrolü: Prompt alanı bulundu ({selector})")
                        return True
                except Exception:
                    continue
            
            # Login butonları veya sayfası varsa giriş yapılmamış
            login_indicators = [
                'button[data-mdc-dialog-action="sign-in"]',
                '[aria-label="Google hesabıyla oturum aç"]',
                '[aria-label="Sign in with Google"]',
                'a[href*="accounts.google.com"]',
            ]
            
            for selector in login_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.debug(f"Login kontrolü: Login butonu bulundu ({selector})")
                        return False
                except Exception:
                    continue
            
            # Sayfa URL'sini kontrol et
            current_url = self.driver.current_url
            if 'accounts.google.com' in current_url:
                logger.debug("Login kontrolü: Google login sayfasında")
                return False
            
            # Varsayılan: yüklenmeyi bekle ve tekrar kontrol et
            return False
            
        except Exception as e:
            logger.warning(f"Login kontrolü hatası: {e}")
            return False
    
    def check_session(self) -> tuple:
        """
        Oturum durumunu kontrol et.
        
        Returns:
            (is_valid, message) tuple'ı
        """
        try:
            if not self.driver:
                return False, "Tarayıcı başlatılmamış"
            
            # Gemini sayfasında mıyız?
            current_url = self.driver.current_url
            if 'gemini.google.com' not in current_url:
                self.navigate_to_gemini()
                time.sleep(GeminiTimeouts.PAGE_LOAD)
            
            # Login kontrolü
            if self.is_logged_in():
                return True, "Oturum aktif"
            else:
                return False, "Oturum kapalı - /login komutu ile giriş yapın"
                
        except Exception as e:
            return False, f"Oturum kontrol hatası: {str(e)}"
    
    def refresh_page(self) -> None:
        """Sayfayı yenile"""
        self.driver.refresh()
        time.sleep(GeminiTimeouts.PAGE_READY)
    
    def start_new_chat(self) -> None:
        """Yeni sohbet başlat"""
        logger.info("Yeni sohbet başlatılıyor...")
        
        try:
            for selector in GeminiSelectors.NEW_CHAT_VARIANTS:
                try:
                    new_chat = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.execute_script("arguments[0].click();", new_chat)
                    time.sleep(GeminiTimeouts.MEDIUM_WAIT)
                    logger.info("Yeni sohbet başlatıldı")
                    return
                except Exception:
                    continue
            
            # Fallback: URL ile yenile
            logger.info("Buton bulunamadı, URL ile yeni sohbet açılıyor...")
            self.driver.get(self.gemini_url)
            time.sleep(GeminiTimeouts.MEDIUM_WAIT)
            self.refresh_page()
            logger.info("Sayfa yenilendi")
            
        except Exception as e:
            logger.warning(f"Yeni sohbet hatası, yenileniyor: {e}")
            self.driver.get(self.gemini_url)
            time.sleep(GeminiTimeouts.PAGE_READY)
    
    def wait_for_element(
        self, 
        selector: str, 
        timeout: int = GeminiTimeouts.ELEMENT_VISIBLE,
        condition: str = "visible"
    ):
        """Element için bekle ve döndür"""
        wait = WebDriverWait(self.driver, timeout)
        
        if condition == "visible":
            return wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, selector)
            ))
        elif condition == "clickable":
            return wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, selector)
            ))
        elif condition == "present":
            return wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, selector)
            ))
        
        raise ValueError(f"Bilinmeyen condition: {condition}")

