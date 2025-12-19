"""
Clipboard İşlemleri Modülü
Fotoğrafları clipboard'a kopyalama işlemleri
"""

import subprocess
import io
from pathlib import Path
from PIL import Image

from .logger import get_logger
from .exceptions import ClipboardError

logger = get_logger(__name__)


def copy_image_to_clipboard(image_path: str) -> bool:
    """
    Fotoğrafı sistem clipboard'ına kopyala.
    
    Linux'ta xclip kullanır. JPG dosyaları otomatik PNG'ye çevrilir.
    
    Args:
        image_path: Kopyalanacak fotoğrafın yolu
    
    Returns:
        Başarılı ise True
    
    Raises:
        ClipboardError: Kopyalama başarısız olduğunda
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise ClipboardError(
            "Dosya bulunamadı",
            details=str(image_path)
        )
    
    try:
        # JPG/JPEG ise PNG'ye çevir (clipboard uyumluluğu)
        if image_path.suffix.lower() in ['.jpg', '.jpeg']:
            return _copy_jpg_as_png(image_path)
        else:
            return _copy_png_direct(image_path)
            
    except subprocess.CalledProcessError as e:
        raise ClipboardError(
            "xclip komutu başarısız",
            details=str(e)
        )
    except Exception as e:
        raise ClipboardError(
            "Clipboard kopyalama hatası",
            details=str(e)
        )


def _copy_jpg_as_png(image_path: Path) -> bool:
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


def _copy_png_direct(image_path: Path) -> bool:
    """PNG dosyasını doğrudan clipboard'a kopyala"""
    logger.debug(f"Doğrudan kopyalama: {image_path}")
    
    cmd = f'xclip -selection clipboard -t image/png -i "{image_path}"'
    subprocess.run(cmd, shell=True, check=True)
    
    logger.info("Fotoğraf clipboard'a kopyalandı")
    return True


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
