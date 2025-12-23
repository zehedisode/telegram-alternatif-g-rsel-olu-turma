"""
Value Object: Prompt
AI prompt'ları için tip güvenliği ve doğrulama sağlar.
"""

from dataclasses import dataclass
from typing import Optional


# Class-level sabitler
_MAX_LENGTH = 10000


@dataclass(frozen=True)
class Prompt:
    """
    Prompt Value Object'i.
    Boş olmayan, maksimum karakter limitli prompt metni.
    """
    
    text: str
    
    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Prompt boş olamaz")
        
        if len(self.text) > _MAX_LENGTH:
            # Frozen olduğu için object.__setattr__ kullanmalıyız
            object.__setattr__(self, 'text', self.text[:_MAX_LENGTH])
    
    @classmethod
    def create(cls, text: Optional[str]) -> Optional["Prompt"]:
        """Güvenli oluşturma - None dönebilir"""
        if not text or not text.strip():
            return None
        return cls(text.strip())
    
    def truncate(self, max_length: int) -> "Prompt":
        """Kısaltılmış yeni prompt döndür"""
        if len(self.text) <= max_length:
            return self
        return Prompt(self.text[:max_length])
    
    def __str__(self) -> str:
        return self.text
    
    def __len__(self) -> int:
        return len(self.text)
