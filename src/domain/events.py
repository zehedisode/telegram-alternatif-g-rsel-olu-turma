"""
Domain Events
Event-driven mimari için domain olayları
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .entities import ProcessStatus, ImageEntity


@dataclass(frozen=True)
class DomainEvent:
    """Temel domain event"""
    event_id: str = field(default_factory=lambda: __import__('uuid').uuid4().hex)
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ImageUploadedEvent(DomainEvent):
    """Görsel yüklendiğinde tetiklenir"""
    session_id: str = ""
    image_path: str = ""
    target_count: int = 1


@dataclass(frozen=True)
class AnalysisCompletedEvent(DomainEvent):
    """Analiz tamamlandığında tetiklenir"""
    session_id: str = ""
    extracted_prompt: str = ""


@dataclass(frozen=True)
class ImageGeneratedEvent(DomainEvent):
    """Yeni görsel oluşturulduğunda tetiklenir"""
    session_id: str = ""
    image_path: str = ""
    image_number: int = 0
    total_count: int = 0


@dataclass(frozen=True)
class ProcessCompletedEvent(DomainEvent):
    """İşlem tamamlandığında tetiklenir"""
    session_id: str = ""
    success: bool = True
    total_images: int = 0
    duration_seconds: int = 0
    error_message: Optional[str] = None


@dataclass(frozen=True)
class StatusChangedEvent(DomainEvent):
    """Durum değiştiğinde tetiklenir"""
    session_id: str = ""
    previous_status: Optional[ProcessStatus] = None
    new_status: Optional[ProcessStatus] = None
    details: str = ""
