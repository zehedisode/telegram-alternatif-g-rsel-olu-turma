"""
Yapılandırma Modülü
Tüm ayarlar merkezi olarak burada tanımlanır
"""

import os
from pathlib import Path

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.absolute()

# Telegram Bot Token (ortam değişkeninden veya varsayılan)
BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "7500254811:AAGPy9JKmzJjw5rr1Dgr9-yRfCAlr8pZ06s"
)

# Chrome profil ayarları
CHROME_PROFILE_PATH = os.environ.get(
    "CHROME_PROFILE_PATH",
    str(PROJECT_ROOT / "chrome_profile")
)
CHROME_PROFILE_NAME = "Default"

# Gemini URL
GEMINI_URL = "https://gemini.google.com/app"

# Fotoğraf kayıt klasörü
IMAGES_DIR = str(PROJECT_ROOT / "images")

# Prompt dosyası yolu
PROMPT_FILE = str(PROJECT_ROOT / "prompt.txt")


def validate_config():
    """Yapılandırmayı doğrula"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN ayarlanmamış")
    
    if not Path(PROMPT_FILE).exists():
        errors.append(f"Prompt dosyası bulunamadı: {PROMPT_FILE}")
    
    # Images klasörünü oluştur
    Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
    
    return errors


def get_prompt_text() -> str:
    """Prompt dosyasını oku"""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""
