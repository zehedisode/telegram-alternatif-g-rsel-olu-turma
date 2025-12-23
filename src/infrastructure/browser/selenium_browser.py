"""
Selenium Browser Servisi
IBrowserService implementasyonu
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

from ...domain import IBrowserService, BrowserError

logger = logging.getLogger(__name__)


class SeleniumBrowserService(IBrowserService):
    """
    Chrome tarayıcı yöneticisi.
    IBrowserService interface'ini implement eder.
    """
    
    def __init__(
        self,
        profile_path: str = None,
        download_dir: str = None,
        headless: bool = False
    ):
        self.profile_path = profile_path
        self.download_dir = download_dir
        self.headless = headless
        self.driver = None
    
    def __enter__(self):
        """Context manager giriş"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager çıkış"""
        self.stop()
        return False
    
    def _create_options(self) -> Options:
        """Chrome seçeneklerini oluştur"""
        options = Options()
        
        # Profil ayarları
        if self.profile_path:
            options.add_argument(f"user-data-dir={self.profile_path}")
        
        # Otomasyon tespitini engelle
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Performans ve stabilite
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Profil kilidi sorununu çöz
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-background-networking")
        
        # Başsız mod
        if self.headless:
            options.add_argument("--headless=new")
        
        # İndirme ayarları
        if self.download_dir:
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
            }
            options.add_experimental_option("prefs", prefs)
        
        return options
    
    def start(self) -> None:
        """Chrome tarayıcısını başlat"""
        if self.driver:
            logger.warning("Tarayıcı zaten çalışıyor")
            return
        
        logger.info("Chrome başlatılıyor...")
        
        try:
            options = self._create_options()
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.maximize_window()
            
            logger.info("Chrome başarıyla başlatıldı")
            
        except Exception as e:
            raise BrowserError(
                "Chrome başlatılamadı",
                details=str(e)
            )
    
    def stop(self) -> None:
        """Tarayıcıyı kapat"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Tarayıcı kapatıldı")
            except Exception as e:
                logger.warning(f"Tarayıcı kapatılırken hata: {e}")
            finally:
                self.driver = None
    
    def navigate_to(self, url: str) -> None:
        """Belirtilen URL'ye git"""
        if not self.driver:
            self.start()
        self.driver.get(url)
    
    def is_running(self) -> bool:
        """Tarayıcı çalışıyor mu?"""
        return self.driver is not None
    
    def get_cookies(self) -> list:
        """Selenium çerezlerini al"""
        if not self.driver:
            return []
        return self.driver.get_cookies()
    
    def get_user_agent(self) -> str:
        """Tarayıcı user agent'ını al"""
        if not self.driver:
            return ""
        return self.driver.execute_script("return navigator.userAgent;")
