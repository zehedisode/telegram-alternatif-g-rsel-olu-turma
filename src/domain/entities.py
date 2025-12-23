"""
Domain Entities
İş mantığının temel varlıkları
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional
from pathlib import Path
import uuid


class ProcessStatus(Enum):
    """İşlem durumu enum'u"""
    PENDING = auto()
    DOWNLOADING = auto()
    BROWSER_STARTING = auto()
    NAVIGATING = auto()
    UPLOADING = auto()
    ANALYZING = auto()
    WAITING_RESPONSE = auto()
    PROMPT_RECEIVED = auto()
    GENERATING = auto()
    DOWNLOADING_RESULT = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(frozen=True)
class ImageEntity:
    """
    Görsel Entitisi - Immutable
    Hem kaynak hem de oluşturulan görseller için kullanılır.
    """
    path: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def exists(self) -> bool:
        """Dosya var mı?"""
        return Path(self.path).exists()
    
    @property
    def filename(self) -> str:
        """Dosya adı"""
        return Path(self.path).name
    
    @property
    def extension(self) -> str:
        """Dosya uzantısı"""
        return Path(self.path).suffix.lower()
    
    def is_valid_image(self) -> bool:
        """Geçerli görsel formatı mı?"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        return self.extension in valid_extensions


@dataclass
class SessionEntity:
    """
    Oturum Entitisi
    Bir kullanıcı işlem oturumunu temsil eder.
    """
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return hash(self.session_id)


@dataclass
class ProcessContext:
    """
    İşlem Bağlamı (Context)
    Bir görsel işleme sürecinin tüm durumunu tutar.
    """
    session: SessionEntity
    original_image: ImageEntity
    target_count: int
    status: ProcessStatus = ProcessStatus.PENDING
    generated_images: List[ImageEntity] = field(default_factory=list)
    extracted_prompt: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @property
    def is_completed(self) -> bool:
        """İşlem tamamlandı mı?"""
        return self.status == ProcessStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """İşlem başarısız mı?"""
        return self.status == ProcessStatus.FAILED
    
    @property
    def completed_count(self) -> int:
        """Tamamlanan görsel sayısı"""
        return len(self.generated_images)
    
    @property
    def progress_percentage(self) -> float:
        """İlerleme yüzdesi"""
        if self.target_count == 0:
            return 0.0
        return (self.completed_count / self.target_count) * 100
    
    def mark_completed(self):
        """İşlemi tamamlandı olarak işaretle"""
        self.status = ProcessStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_failed(self, error: str):
        """İşlemi başarısız olarak işaretle"""
        self.status = ProcessStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()
    
    def add_generated_image(self, image: ImageEntity):
        """Oluşturulan görsel ekle"""
        self.generated_images.append(image)



