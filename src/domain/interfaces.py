"""
Domain Interfaces
Dependency Inversion için abstract interface'ler
Infrastructure bu interface'leri implement eder.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Callable, Awaitable
from .entities import ImageEntity, ProcessContext, ProcessStatus


class IBrowserService(ABC):
    """Tarayıcı otomasyonu için arayüz"""
    
    @abstractmethod
    def start(self) -> None:
        """Tarayıcıyı başlat"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Tarayıcıyı kapat"""
        pass

    @abstractmethod
    def navigate_to(self, url: str) -> None:
        """Belirtilen URL'ye git"""
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Tarayıcı çalışıyor mu?"""
        pass
    
    @abstractmethod
    def get_cookies(self) -> list:
        """Çerezleri döndür"""
        pass
    
    @abstractmethod
    def get_user_agent(self) -> str:
        """User agent döndür"""
        pass


class IClipboardService(ABC):
    """Clipboard işlemleri için arayüz"""
    
    @abstractmethod
    def copy_image(self, image_path: str) -> bool:
        """Görseli clipboard'a kopyala"""
        pass


class IImageDownloader(ABC):
    """Görsel indirme için arayüz"""
    
    @abstractmethod
    def download(self) -> Optional[str]:
        """Görseli indir, dosya yolunu döndür"""
        pass


class IAIService(ABC):
    """AI (Gemini) servisleri için arayüz"""
    
    @abstractmethod
    def analyze_image(self, image: ImageEntity, prompt: str) -> str:
        """Görseli analiz eder ve bir prompt döner"""
        pass

    @abstractmethod
    def generate_image(self, prompt: str) -> ImageEntity:
        """Prompt kullanarak yeni bir görsel oluşturur"""
        pass
    
    @abstractmethod
    def start_new_session(self) -> None:
        """Yeni AI oturumu başlat"""
        pass


# Progress callback tipi
ProgressCallback = Callable[[ProcessStatus, str], Awaitable[None]]


class IBotGateway(ABC):
    """Bot (Telegram) iletişimi için arayüz"""
    
    @abstractmethod
    async def send_message(self, chat_id: str, text: str) -> None:
        """Mesaj gönder"""
        pass

    @abstractmethod
    async def send_image(
        self, 
        chat_id: str, 
        image: ImageEntity, 
        caption: Optional[str] = None
    ) -> None:
        """Görsel gönder"""
        pass
    
    @abstractmethod
    async def update_message(self, chat_id: str, message_id: str, text: str) -> None:
        """Mevcut mesajı güncelle"""
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str, destination: str) -> str:
        """Bot'a gönderilen dosyayı indir"""
        pass


class IProgressNotifier(ABC):
    """İlerleme bildirimi için arayüz"""
    
    @abstractmethod
    async def notify_step(self, status: ProcessStatus, extra_info: str = "") -> None:
        """Adımı bildir"""
        pass
    
    @abstractmethod
    async def notify_image_progress(self, current: int, total: int) -> None:
        """Görsel üretim ilerlemesini bildir"""
        pass
    
    @abstractmethod
    async def notify_complete(self, success: bool, details: str = "") -> None:
        """Tamamlanma durumunu bildir"""
        pass


class IConfigProvider(ABC):
    """Yapılandırma sağlayıcı arayüzü"""
    
    @property
    @abstractmethod
    def bot_token(self) -> str:
        pass
    
    @property
    @abstractmethod
    def gemini_url(self) -> str:
        pass
    
    @property
    @abstractmethod
    def chrome_profile_path(self) -> str:
        pass
    
    @property
    @abstractmethod
    def images_dir(self) -> str:
        pass
    
    @property
    @abstractmethod
    def prompt_text(self) -> str:
        pass
