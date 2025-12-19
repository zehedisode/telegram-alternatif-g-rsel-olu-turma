"""
Özel Exception Sınıfları
Otomasyon sisteminde kullanılan hata tipleri
"""


class AutomationError(Exception):
    """Ana otomasyon hatası - tüm özel hataların base class'ı"""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Detay: {self.details}"
        return self.message


class BrowserError(AutomationError):
    """Tarayıcı ile ilgili hatalar"""
    pass


class ClipboardError(AutomationError):
    """Clipboard işlem hataları"""
    pass


class DownloadError(AutomationError):
    """Dosya indirme hataları"""
    pass


class GeminiError(AutomationError):
    """Gemini etkileşim hataları"""
    pass


class NavigationError(GeminiError):
    """Sayfa navigasyon hataları"""
    pass


class ResponseError(GeminiError):
    """Yanıt alma hataları"""
    pass


class ImageGenerationError(GeminiError):
    """Görsel oluşturma hataları"""
    pass
