#!/usr/bin/env python3
"""
Telegram-Gemini Otomasyon Sistemi
Ana çalıştırıcı dosya

Kullanım:
    python main.py

Bu script:
1. Telegram bot'unu başlatır
2. Gelen fotoğrafları dinler
3. Fotoğraf gelince Chrome'u açar
4. Gemini'ye gidip fotoğrafı yükler
5. Belirlenen prompt'u gönderir
"""

import logging
from telegram_bot import run_bot

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("🤖 Telegram-Gemini Otomasyon Sistemi")
    print("=" * 50)
    print()
    print("📌 Talimatlar:")
    print("1. Telegram'da bot'unuza gidin")
    print("2. /start komutu ile başlayın")
    print("3. Bir fotoğraf gönderin")
    print("4. Chrome açılacak ve Gemini'ye yükleyecek")
    print()
    print("⚠️  Not: İlk kullanımda Chrome profilinizle")
    print("    Gemini'de giriş yapmış olmanız gerekiyor.")
    print()
    print("Durdurmak için Ctrl+C yapın.")
    print("=" * 50)
    print()
    
    try:
        # Bot'u başlat
        run_bot()
    except KeyboardInterrupt:
        print("\n\n👋 Bot durduruldu.")
    except Exception as e:
        logger.error(f"Hata: {e}")
        raise


if __name__ == "__main__":
    main()
