"""
Görsel İndirme Servisi
IImageDownloader implementasyonu
"""

import os
import time
import uuid
import shutil
from pathlib import Path
from typing import Optional
import logging

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...domain import IImageDownloader, DownloadError
from .gemini.scripts import GeminiScripts

logger = logging.getLogger(__name__)


class ImageDownloaderService(IImageDownloader):
    """
    Gemini'den görsel indirme servisi.
    Birden fazla yöntem dener: requests, buton, Chrome indirme.
    """
    
    def __init__(self, driver: webdriver.Chrome, download_dir: str):
        self.driver = driver
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self) -> Optional[str]:
        """
        Oluşturulan görseli indir.
        Önce requests ile dener, başarısız olursa buton yöntemine geçer.
        """
        logger.info("Görsel indiriliyor...")
        
        # Görselin tam yüklenmesini bekle
        time.sleep(3)
        
        # URL'yi bul
        image_url = self._find_image_url()
        if not image_url:
            raise DownloadError("Görsel URL'si bulunamadı")
        
        logger.info(f"Görsel URL bulundu: {image_url[:80]}...")
        
        # En yüksek kaliteyi al
        image_url = self._get_high_quality_url(image_url)
        
        # Yöntem 1: Requests ile indir
        try:
            return self._download_via_requests(image_url)
        except Exception as e:
            logger.warning(f"Requests yöntemi başarısız: {e}")
        
        # Yöntem 2: Buton ile indir
        try:
            return self._download_via_button()
        except Exception as e:
            logger.warning(f"Buton yöntemi başarısız: {e}")
        
        # Yöntem 3: Chrome indirmelerini kontrol et
        try:
            return self._find_chrome_download()
        except Exception as e:
            logger.warning(f"Chrome indirme kontrolü başarısız: {e}")
        
        raise DownloadError("Tüm indirme yöntemleri başarısız oldu")
    
    def _find_image_url(self) -> Optional[str]:
        """JavaScript ile görsel URL'sini bul"""
        try:
            return self.driver.execute_script(GeminiScripts.FIND_IMAGE_URL)
        except Exception:
            return None
    
    def _get_high_quality_url(self, url: str) -> str:
        """URL'den en yüksek kaliteyi al"""
        if '=' in url:
            base_url = url.split('=')[0]
            return f"{base_url}=s4096"
        return url
    
    def _download_via_requests(self, url: str) -> str:
        """Requests kütüphanesi ile indir"""
        logger.info("Selenium çerezleri ile indiriliyor...")
        
        session = requests.Session()
        
        # Çerezleri aktar
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Headers ayarla
        user_agent = self.driver.execute_script(GeminiScripts.GET_USER_AGENT)
        headers = {
            'User-Agent': user_agent,
            'Referer': 'https://gemini.google.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        # İndir
        response = session.get(url, headers=headers, timeout=60)
        logger.info(f"HTTP yanıt kodu: {response.status_code}")
        
        if response.status_code != 200:
            raise DownloadError(f"HTTP hatası: {response.status_code}")
        
        # Kaydet
        file_name = f"generated_{uuid.uuid4().hex[:8]}.png"
        file_path = self.download_dir / file_name
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Görsel indirildi: {file_path}")
        return str(file_path)
    
    def _download_via_button(self) -> str:
        """İndirme butonuna tıklayarak indir"""
        logger.info("Buton yöntemi deneniyor...")
        
        wait = WebDriverWait(self.driver, 20)
        
        # Görsele tıkla (büyütmek için)
        try:
            image_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button.image-button, .generated-image-button')
            ))
            image_button.click()
            time.sleep(2)
        except Exception:
            pass
        
        # İndirme butonlarını dene
        download_selectors = [
            'button[aria-label="Tam boyutlu resmi indir"]',
            'button[aria-label*="indir"]',
            'button[aria-label*="download"]',
        ]
        
        for selector in download_selectors:
            try:
                download_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                self.driver.execute_script("arguments[0].click();", download_button)
                time.sleep(5)
                logger.info("İndirme butonu tıklandı")
                
                return self._find_chrome_download()
            except Exception:
                continue
        
        raise DownloadError("İndirme butonu bulunamadı")
    
    def _find_chrome_download(self) -> str:
        """Chrome'un indirdiği en son dosyayı bul"""
        search_dirs = [
            self.download_dir,
            Path.home() / "İndirilenler",
            Path.home() / "Downloads"
        ]
        
        latest_file = None
        latest_time = 0
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for f in search_dir.iterdir():
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                    file_time = f.stat().st_ctime
                    
                    # Son 30 saniye içinde oluşturulmuş
                    if time.time() - file_time < 30 and file_time > latest_time:
                        latest_time = file_time
                        latest_file = f
        
        if not latest_file:
            raise DownloadError("İndirilen dosya bulunamadı")
        
        # Gerekirse taşı
        if latest_file.parent != self.download_dir:
            new_name = f"generated_{uuid.uuid4().hex[:8]}.png"
            new_path = self.download_dir / new_name
            shutil.move(str(latest_file), str(new_path))
            logger.info(f"Dosya taşındı: {new_path}")
            return str(new_path)
        
        return str(latest_file)
