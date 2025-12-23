"""
Application DTOs (Data Transfer Objects)
Katmanlar arası veri taşıma nesneleri
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ImageProcessRequest:
    """Görsel işleme isteği"""
    chat_id: str
    user_id: str
    image_path: str
    target_count: int
    message_id: Optional[str] = None


@dataclass
class ImageProcessResult:
    """Görsel işleme sonucu"""
    success: bool
    generated_image_paths: List[str] = field(default_factory=list)
    extracted_prompt: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: int = 0
    
    @property
    def image_count(self) -> int:
        return len(self.generated_image_paths)


@dataclass
class ProgressUpdate:
    """İlerleme güncellemesi"""
    step_name: str
    step_emoji: str
    current_step: int
    total_steps: int
    current_image: int = 0
    total_images: int = 0
    extra_info: str = ""
    elapsed_seconds: int = 0


@dataclass
class BotMessageRequest:
    """Bot mesaj isteği"""
    chat_id: str
    text: str
    parse_mode: str = "Markdown"
    reply_to_message_id: Optional[str] = None


@dataclass
class BotImageRequest:
    """Bot görsel gönderme isteği"""
    chat_id: str
    image_path: str
    caption: Optional[str] = None
    as_document: bool = False
