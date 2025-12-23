"""
Src Package
Clean Architecture Telegram Görsel Otomasyon Botu
"""

from .container import get_container, Container
from .presentation import run_bot

__all__ = ["get_container", "Container", "run_bot"]
