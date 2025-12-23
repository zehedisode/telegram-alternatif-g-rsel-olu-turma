"""
Domain Layer
İş mantığı çekirdeği - dış bağımlılık yok
"""

from .entities import (
    ProcessStatus,
    ImageEntity,
    SessionEntity,
    ProcessContext,

)

from .exceptions import (
    DomainException,
    ValidationError,
    ImageProcessingError,
    BrowserError,
    ClipboardError,
    DownloadError,
    AIServiceError,
    NavigationError,
    ResponseError,
    ImageGenerationError,
    BotGatewayError,
    ConfigurationError,
)

from .interfaces import (
    IBrowserService,
    IClipboardService,
    IImageDownloader,
    IAIService,
    IBotGateway,
    IProgressNotifier,
    IConfigProvider,
    ProgressCallback,
)

from .value_objects import ImageCount, Prompt

from .events import (
    DomainEvent,
    ImageUploadedEvent,
    AnalysisCompletedEvent,
    ImageGeneratedEvent,
    ProcessCompletedEvent,
    StatusChangedEvent,
)

__all__ = [
    # Entities
    "ProcessStatus",
    "ImageEntity",
    "SessionEntity",
    "ProcessContext",
    # Exceptions
    "DomainException",
    "ValidationError",
    "ImageProcessingError",
    "BrowserError",
    "ClipboardError",
    "DownloadError",
    "AIServiceError",
    "NavigationError",
    "ResponseError",
    "ImageGenerationError",
    "BotGatewayError",
    "ConfigurationError",
    # Interfaces
    "IBrowserService",
    "IClipboardService",
    "IImageDownloader",
    "IAIService",
    "IBotGateway",
    "IProgressNotifier",
    "IConfigProvider",
    "ProgressCallback",
    # Value Objects
    "ImageCount",
    "Prompt",
    # Events
    "DomainEvent",
    "ImageUploadedEvent",
    "AnalysisCompletedEvent",
    "ImageGeneratedEvent",
    "ProcessCompletedEvent",
    "StatusChangedEvent",
]
