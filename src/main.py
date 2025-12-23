#!/usr/bin/env python3
"""
Clean Architecture Telegram-Gemini Otomasyon Sistemi
Ana çalıştırıcı dosya

Kullanım:
    python -m src.main
    # veya
    python src/main.py

Bu script:
1. Telegram bot'unu başlatır
2. Gelen fotoğrafları dinler
3. Fotoğraf gelince Chrome'u açar
4. Gemini'ye gidip fotoğrafı yükler
5. Belirlenen prompt'u gönderir
6. Oluşturulan görselleri kullanıcıya gönderir
"""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.presentation import run_bot
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("🤖 Clean Architecture Telegram-Gemini Bot")
    print("=" * 50)
    print()
    print("📌 Talimatlar:")
    print("1. Telegram'da bot'unuza gidin")
    print("2. /start komutu ile başlayın")
    print("3. Bir fotoğraf gönderin")
    print("4. Kaç adet görsel istediğinizi belirtin (1-9)")
    print("5. AI görselleri oluşturacak ve gönderecek")
    print()
    print("⚠️  Not: İlk kullanımda Chrome profilinizle")
    print("    Gemini'de giriş yapmış olmanız gerekiyor.")
    print()
    print("Durdurmak için Ctrl+C yapın.")
    print("=" * 50)
    print()
    
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n\n👋 Bot durduruldu.")
    except Exception as e:
        logger.error(f"Hata: {e}")
        raise


if __name__ == "__main__":
    main()
