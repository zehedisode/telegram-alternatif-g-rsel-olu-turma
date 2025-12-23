"""
Domain Exceptions
İş mantığına özgü hata tipleri - merkezi hata yönetimi
"""


class DomainException(Exception):
    """Domain katmanına özgü temel hata"""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Detay: {self.details}"
        return self.message


class ValidationError(DomainException):
    """Doğrulama hatası"""
    pass


class ImageProcessingError(DomainException):
    """Görsel işleme hatası"""
    pass


class BrowserError(DomainException):
    """Tarayıcı ile ilgili hatalar"""
    pass


class ClipboardError(DomainException):
    """Clipboard işlem hataları"""
    pass


class DownloadError(DomainException):
    """Dosya indirme hataları"""
    pass


class AIServiceError(DomainException):
    """AI servis hataları - temel"""
    pass


class NavigationError(AIServiceError):
    """Sayfa navigasyon hataları"""
    pass


class ResponseError(AIServiceError):
    """Yanıt alma hataları"""
    pass


class ImageGenerationError(AIServiceError):
    """Görsel oluşturma hataları"""
    pass


class BotGatewayError(DomainException):
    """Bot iletişim hataları"""
    pass


class ConfigurationError(DomainException):
    """Yapılandırma hataları"""
    pass
