"""
Value Object: ImageCount
Görsel sayısı için tip güvenliği ve doğrulama sağlar.
"""

from dataclasses import dataclass


# Class-level sabitler
_MIN_COUNT = 1
_MAX_COUNT = 9


@dataclass(frozen=True)
class ImageCount:
    """
    Görsel sayısı Value Object'i.
    1-9 arasında bir değer alır ve immutable'dır.
    """
    
    value: int
    
    def __post_init__(self):
        if not isinstance(self.value, int):
            raise ValueError(f"ImageCount tam sayı olmalıdır, alınan: {type(self.value)}")
        
        if self.value < _MIN_COUNT or self.value > _MAX_COUNT:
            raise ValueError(
                f"ImageCount {_MIN_COUNT}-{_MAX_COUNT} arasında olmalıdır, "
                f"alınan: {self.value}"
            )
    
    @classmethod
    def from_string(cls, value: str) -> "ImageCount":
        """String'den ImageCount oluştur"""
        try:
            return cls(int(value.strip()))
        except ValueError as e:
            raise ValueError(f"Geçersiz görsel sayısı: {value}") from e
    
    def __int__(self) -> int:
        return self.value
    
    def __str__(self) -> str:
        return str(self.value)

