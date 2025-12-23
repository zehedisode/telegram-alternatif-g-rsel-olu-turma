"""
Yapılandırma Servisi
IConfigProvider implementasyonu
"""

import os
from pathlib import Path
import logging

from ...domain import IConfigProvider, ConfigurationError

logger = logging.getLogger(__name__)


class ConfigService(IConfigProvider):
    """
    Merkezi yapılandırma servisi.
    Ortam değişkenlerinden ve dosyalardan yapılandırma okur.
    """
    
    def __init__(self, project_root: Path = None):
        self._project_root = project_root or Path(__file__).parents[3]
        self._prompt_text_cache: str = None
    
    @property
    def bot_token(self) -> str:
        """Telegram bot token'ı"""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        
        # Fallback to old config if exists
        if not token:
            try:
                import sys
                sys.path.insert(0, str(self._project_root))
                import config as old_config
                token = old_config.BOT_TOKEN
            except Exception:
                pass
        
        if not token:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN ayarlanmamış")
        
        return token
    
    @property
    def gemini_url(self) -> str:
        """Gemini URL'si"""
        return os.environ.get(
            "GEMINI_URL",
            "https://gemini.google.com/app"
        )
    
    @property
    def chrome_profile_path(self) -> str:
        """Chrome profil yolu"""
        default_path = str(self._project_root / "chrome_profile")
        return os.environ.get("CHROME_PROFILE_PATH", default_path)
    
    @property
    def images_dir(self) -> str:
        """Görseller dizini"""
        default_path = str(self._project_root / "images")
        path = os.environ.get("IMAGES_DIR", default_path)
        
        # Dizini oluştur
        Path(path).mkdir(parents=True, exist_ok=True)
        
        return path
    
    @property
    def prompt_file(self) -> str:
        """Prompt dosya yolu"""
        return str(self._project_root / "prompt.txt")
    
    @property
    def prompt_text(self) -> str:
        """Prompt metni"""
        if self._prompt_text_cache:
            return self._prompt_text_cache
        
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                self._prompt_text_cache = f.read()
                return self._prompt_text_cache
        except FileNotFoundError:
            logger.warning(f"Prompt dosyası bulunamadı: {self.prompt_file}")
            return ""
    
    def validate(self) -> list:
        """Yapılandırmayı doğrula, hata listesi döndür"""
        errors = []
        
        try:
            _ = self.bot_token
        except ConfigurationError as e:
            errors.append(str(e))
        
        if not Path(self.prompt_file).exists():
            errors.append(f"Prompt dosyası bulunamadı: {self.prompt_file}")
        
        return errors
