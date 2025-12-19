"""
Gemini Etkileşim Servisi
Gemini ile sayfa navigasyonu, prompt gönderme, yanıt alma ve görsel oluşturma
"""

import time
from typing import Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from core.logger import get_logger
from core.exceptions import (
    GeminiError,
    NavigationError,
    ResponseError,
    ImageGenerationError,
)
from core.clipboard import copy_image_to_clipboard
from core.downloader import ImageDownloader

logger = get_logger(__name__)


class GeminiService:
    """
    Gemini etkileşim servisi.
    Fotoğraf analizi, prompt üretimi ve görsel oluşturma işlemlerini yönetir.
    """
    
    # CSS Selektörleri
    SELECTORS = {
        'prompt_area': 'div[role="textbox"][aria-label="Buraya istem girin"], .ql-editor',
        'send_button': 'button.send-button, button[aria-label="Mesaj gönder"]',
        'stop_button': 'button[aria-label="Yanıtı durdur"]',
        'model_response': 'model-response',
        'copy_button': 'button[aria-label="Kopyala"]',
        'image_button': 'button.image-button img, .generated-image img',
        'new_chat_selectors': [
            'button[aria-label="Yeni sohbet"]',
            'button[aria-label="New chat"]',
            'button[class*="side-nav-action-"]',
            'a[href="/app"]',
        ],
    }
    
    def __init__(
        self,
        driver: webdriver.Chrome,
        gemini_url: str,
        download_dir: str
    ):
        """
        Args:
            driver: Selenium WebDriver instance
            gemini_url: Gemini sayfa URL'si
            download_dir: İndirme klasörü yolu
        """
        self.driver = driver
        self.gemini_url = gemini_url
        self.download_dir = Path(download_dir)
        self.downloader = ImageDownloader(driver, download_dir)
    
    def go_to_gemini(self) -> bool:
        """Gemini sayfasına git"""
        logger.info("Gemini'ye gidiliyor...")
        
        try:
            self.driver.get(self.gemini_url)
            time.sleep(5)
            logger.info("Gemini sayfası açıldı")
            return True
        except Exception as e:
            raise NavigationError("Gemini'ye gidilemedi", details=str(e))
    
    def start_new_chat(self) -> bool:
        """Yeni sohbet başlat"""
        logger.info("Yeni sohbet başlatılıyor...")
        
        try:
            for selector in self.SELECTORS['new_chat_selectors']:
                try:
                    new_chat = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.execute_script("arguments[0].click();", new_chat)
                    time.sleep(2)
                    logger.info("Yeni sohbet başlatıldı")
                    return True
                except Exception:
                    continue
            
            # Alternatif: URL ile yenile
            logger.info("Buton bulunamadı, URL ile yeni sohbet açılıyor...")
            self.driver.get(self.gemini_url)
            time.sleep(2)
            self.driver.refresh()
            time.sleep(3)
            logger.info("Sayfa yenilendi")
            return True
            
        except Exception as e:
            logger.warning(f"Yeni sohbet hatası, yenileniyor: {e}")
            self.driver.get(self.gemini_url)
            time.sleep(3)
            return True
    
    def upload_image(self, image_path: str) -> bool:
        """Fotoğrafı clipboard yöntemiyle yükle"""
        logger.info(f"Fotoğraf yükleniyor: {image_path}")
        
        try:
            wait = WebDriverWait(self.driver, 30)
            
            # Clipboard'a kopyala
            copy_image_to_clipboard(image_path)
            time.sleep(2)
            
            # Prompt alanına tıkla
            prompt_area = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self.SELECTORS['prompt_area'])
            ))
            prompt_area.click()
            time.sleep(1)
            
            # Ctrl+V ile yapıştır
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            
            logger.info("Fotoğraf yapıştırıldı, yüklenmesi bekleniyor...")
            time.sleep(5)
            
            # Doğrulama
            for _ in range(10):
                try:
                    uploaded = self.driver.execute_script("""
                        const imgs = document.querySelectorAll('img[src*="blob:"], img[src*="data:"], .uploaded-image, .image-preview');
                        return imgs.length > 0;
                    """)
                    if uploaded:
                        logger.info("Fotoğraf yüklendi ve doğrulandı!")
                        time.sleep(2)
                        return True
                except Exception:
                    pass
                time.sleep(1)
            
            logger.warning("Fotoğraf yüklemesi doğrulanamadı, devam ediliyor...")
            return True
            
        except Exception as e:
            raise GeminiError("Fotoğraf yüklenemedi", details=str(e))
    
    def send_prompt(self, prompt_text: str) -> bool:
        """Prompt gönder"""
        logger.info("Prompt gönderiliyor...")
        
        try:
            wait = WebDriverWait(self.driver, 20)
            time.sleep(1)
            
            # JavaScript ile prompt yaz
            self.driver.execute_script("""
                const editor = document.querySelector('.ql-editor p') || document.querySelector('.ql-editor');
                if (editor) {
                    if (editor.tagName === 'P') {
                        editor.innerText = arguments[0];
                    } else {
                        const p = document.createElement('p');
                        p.innerText = arguments[0];
                        editor.appendChild(p);
                    }
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                }
            """, prompt_text)
            
            time.sleep(2)
            
            # Gönder butonuna tıkla
            send_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self.SELECTORS['send_button'])
            ))
            self.driver.execute_script("arguments[0].click();", send_button)
            
            logger.info("Prompt gönderildi!")
            return True
            
        except Exception as e:
            raise GeminiError("Prompt gönderilemedi", details=str(e))
    
    def wait_for_response(self, timeout: int = 120) -> bool:
        """Cevabı bekle"""
        logger.info("Cevap bekleniyor...")
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            time.sleep(5)
            
            # Stop butonunun kaybolmasını bekle
            try:
                wait.until_not(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.SELECTORS['stop_button'])
                ))
            except Exception:
                pass
            
            time.sleep(3)
            logger.info("Cevap alındı!")
            return True
            
        except Exception as e:
            raise ResponseError("Cevap beklenirken hata", details=str(e))
    
    def get_response_text(self) -> Optional[str]:
        """Son cevabı al"""
        logger.info("Cevap metni alınıyor...")
        
        try:
            responses = self.driver.find_elements(
                By.CSS_SELECTOR, self.SELECTORS['model_response']
            )
            if responses:
                text_content = responses[-1].text
                logger.info(f"Cevap alındı: {text_content[:100]}...")
                return text_content
            
            return None
            
        except Exception as e:
            raise ResponseError("Cevap metni alınamadı", details=str(e))
    
    def wait_for_image_generation(self, timeout: int = 180) -> bool:
        """Görsel oluşturulmasını bekle"""
        logger.info("Görsel oluşturulması bekleniyor...")
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.SELECTORS['image_button'])
            ))
            
            time.sleep(3)
            logger.info("Görsel oluşturuldu!")
            return True
            
        except Exception as e:
            raise ImageGenerationError(
                "Görsel oluşturulamadı veya timeout",
                details=str(e)
            )
    
    def download_generated_image(self) -> Optional[str]:
        """Oluşturulan görseli indir"""
        return self.downloader.download()
    
    def full_workflow(self, image_path: str, prompt_text: str) -> Optional[str]:
        """
        Tam akış:
        1. Fotoğraf + prompt gönder
        2. Cevabı bekle ve al
        3. Yeni sohbet aç
        4. Görsel oluşturma promptunu gönder
        5. Görseli indir ve yolunu döndür
        """
        logger.info("=" * 50)
        logger.info("TAM AKIŞ BAŞLIYOR")
        logger.info("=" * 50)
        
        # 1. Gemini'ye git
        self.go_to_gemini()
        
        # 2. Fotoğrafı yükle
        self.upload_image(image_path)
        
        # 3. Ana promptu gönder
        self.send_prompt(prompt_text)
        
        # 4. Cevabı bekle
        self.wait_for_response(timeout=120)
        
        # 5. Cevabı al
        response_text = self.get_response_text()
        if not response_text:
            raise ResponseError("Cevap alınamadı")
        
        logger.info(f"Gemini'den alınan prompt: {response_text[:200]}...")
        
        # 6. Yeni sohbet başlat
        self.start_new_chat()
        
        # 7. Görsel oluşturma promptunu gönder
        self.send_prompt(response_text)
        
        # 8. Görsel oluşturulmasını bekle
        self.wait_for_image_generation(timeout=180)
        
        # 9. Görseli indir
        downloaded_image = self.download_generated_image()
        
        if downloaded_image:
            logger.info(f"İşlem tamamlandı! Görsel: {downloaded_image}")
            return downloaded_image
        
        raise GeminiError("Görsel indirilemedi")
