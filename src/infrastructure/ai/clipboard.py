"""
Clipboard Servisi
IClipboardService implementasyonu
"""

import subprocess
import io
from pathlib import Path
import logging

from PIL import Image

from ...domain import IClipboardService, ClipboardError

logger = logging.getLogger(__name__)


class ClipboardService(IClipboardService):
    """
    Sistem clipboard'ı ile etkileşim servisi.
    Linux'ta xclip kullanır.
    """
    
    def copy_image(self, image_path: str) -> bool:
        """
        Görseli sistem clipboard'ına kopyala.
        JPG dosyaları otomatik PNG'ye çevrilir.
        """
        path = Path(image_path)
        
        if not path.exists():
            raise ClipboardError("Dosya bulunamadı", details=str(path))
        
        try:
            # JPG/JPEG ise PNG'ye çevir
            if path.suffix.lower() in ['.jpg', '.jpeg']:
                return self._copy_jpg_as_png(path)
            else:
                return self._copy_png_direct(path)
                
        except subprocess.CalledProcessError as e:
            raise ClipboardError("xclip komutu başarısız", details=str(e))
        except Exception as e:
            raise ClipboardError("Clipboard kopyalama hatası", details=str(e))
    
    def _copy_jpg_as_png(self, image_path: Path) -> bool:
        """JPG dosyasını PNG olarak clipboard'a kopyala"""
        logger.debug(f"JPG→PNG dönüşümü: {image_path}")
        
        img = Image.open(image_path)
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_buffer.seek(0)
        
        process = subprocess.Popen(
            ['xclip', '-selection', 'clipboard', '-t', 'image/png'],
            stdin=subprocess.PIPE
        )
        process.communicate(input=png_buffer.read())
        
        if process.returncode != 0:
            raise ClipboardError("xclip sıfır olmayan kod döndürdü")
        
        logger.info("Fotoğraf clipboard'a kopyalandı (JPG→PNG)")
        return True
    
    def _copy_png_direct(self, image_path: Path) -> bool:
        """PNG dosyasını doğrudan clipboard'a kopyala"""
        logger.debug(f"Doğrudan kopyalama: {image_path}")
        
        cmd = f'xclip -selection clipboard -t image/png -i "{image_path}"'
        subprocess.run(cmd, shell=True, check=True)
        
        logger.info("Fotoğraf clipboard'a kopyalandı")
        return True
    
    @staticmethod
    def check_xclip_installed() -> bool:
        """xclip'in yüklü olup olmadığını kontrol et"""
        try:
            subprocess.run(
                ['xclip', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
