"""
Handler Registry
Command ve Message handler'ların otomatik kaydı için registry sistemi.
OCP: Yeni handler = yeni decorator, mevcut koda dokunma yok.
"""

import logging
from typing import Callable, Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum, auto

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

logger = logging.getLogger(__name__)


class HandlerType(Enum):
    """Handler tipleri"""
    COMMAND = auto()
    MESSAGE = auto()
    CALLBACK_QUERY = auto()
    CONVERSATION = auto()


@dataclass
class HandlerConfig:
    """Handler konfigürasyonu"""
    handler_type: HandlerType
    name: str
    handler_func: Callable
    filter_obj: Any = None
    priority: int = 0
    group: int = 0


@dataclass
class ConversationConfig:
    """Conversation handler konfigürasyonu"""
    name: str
    entry_points: List[HandlerConfig] = field(default_factory=list)
    states: Dict[int, List[HandlerConfig]] = field(default_factory=dict)
    fallbacks: List[HandlerConfig] = field(default_factory=list)


class HandlerRegistry:
    """
    Handler Registry - OCP Uyumlu.
    
    Decorator pattern ile handler'ların otomatik kaydı:
    
    @registry.command("start")
    async def start_handler(update, context):
        ...
    
    @registry.message(filters.PHOTO)
    async def photo_handler(update, context):
        ...
    """
    
    _instance: Optional["HandlerRegistry"] = None
    
    def __init__(self):
        self._handlers: List[HandlerConfig] = []
        self._conversations: List[ConversationConfig] = []
    
    @classmethod
    def get_instance(cls) -> "HandlerRegistry":
        """Singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Registry'yi sıfırla (test için)"""
        cls._instance = None
    
    def command(
        self, 
        command_name: str, 
        priority: int = 0,
        group: int = 0
    ) -> Callable:
        """
        Command handler decorator.
        
        Kullanım:
            @registry.command("start")
            async def start_handler(update, context):
                ...
        """
        def decorator(func: Callable) -> Callable:
            config = HandlerConfig(
                handler_type=HandlerType.COMMAND,
                name=command_name,
                handler_func=func,
                priority=priority,
                group=group,
            )
            self._handlers.append(config)
            logger.debug(f"Command kaydedildi: /{command_name}")
            return func
        return decorator
    
    def message(
        self, 
        filter_obj: Any,
        priority: int = 0,
        group: int = 0
    ) -> Callable:
        """
        Message handler decorator.
        
        Kullanım:
            @registry.message(filters.PHOTO)
            async def photo_handler(update, context):
                ...
        """
        def decorator(func: Callable) -> Callable:
            config = HandlerConfig(
                handler_type=HandlerType.MESSAGE,
                name=func.__name__,
                handler_func=func,
                filter_obj=filter_obj,
                priority=priority,
                group=group,
            )
            self._handlers.append(config)
            logger.debug(f"Message handler kaydedildi: {func.__name__}")
            return func
        return decorator
    
    def register_command(
        self, 
        command_name: str, 
        handler_func: Callable,
        priority: int = 0,
        group: int = 0
    ) -> None:
        """Manuel command kaydı"""
        config = HandlerConfig(
            handler_type=HandlerType.COMMAND,
            name=command_name,
            handler_func=handler_func,
            priority=priority,
            group=group,
        )
        self._handlers.append(config)
    
    def register_message_handler(
        self, 
        handler_func: Callable,
        filter_obj: Any,
        priority: int = 0,
        group: int = 0
    ) -> None:
        """Manuel message handler kaydı"""
        config = HandlerConfig(
            handler_type=HandlerType.MESSAGE,
            name=handler_func.__name__,
            handler_func=handler_func,
            filter_obj=filter_obj,
            priority=priority,
            group=group,
        )
        self._handlers.append(config)
    
    def register_conversation(self, config: ConversationConfig) -> None:
        """Conversation handler kaydı"""
        self._conversations.append(config)
        logger.debug(f"Conversation kaydedildi: {config.name}")
    
    def apply_to_application(self, app: Application) -> None:
        """
        Tüm kayıtlı handler'ları application'a ekle.
        
        Args:
            app: Telegram Application instance
        """
        # Önceliğe göre sırala
        sorted_handlers = sorted(
            self._handlers, 
            key=lambda h: h.priority, 
            reverse=True
        )
        
        for config in sorted_handlers:
            handler = self._create_handler(config)
            if handler:
                app.add_handler(handler, group=config.group)
                logger.info(f"Handler eklendi: {config.name}")
        
        # Conversation handler'ları ekle
        for conv_config in self._conversations:
            conv_handler = self._create_conversation_handler(conv_config)
            app.add_handler(conv_handler)
            logger.info(f"Conversation eklendi: {conv_config.name}")
    
    def discover_handlers(
        self, 
        package: str = "src.presentation.handlers"
    ) -> int:
        """
        Handler modüllerini otomatik keşfet ve import et.
        
        OCP: Yeni handler = yeni dosya, registry değişikliği yok.
        
        Args:
            package: Handler'ların bulunduğu package
            
        Returns:
            Keşfedilen handler modül sayısı
        """
        import importlib
        import pkgutil
        from pathlib import Path
        
        discovered = 0
        
        try:
            pkg = importlib.import_module(package)
            pkg_path = Path(pkg.__file__).parent
            
            for _, module_name, _ in pkgutil.iter_modules([str(pkg_path)]):
                # __init__ ve registry'yi atla
                if module_name.startswith('_') or module_name == 'handler_registry':
                    continue
                
                try:
                    importlib.import_module(f"{package}.{module_name}")
                    discovered += 1
                    logger.debug(f"Handler modülü yüklendi: {module_name}")
                except Exception as e:
                    logger.warning(f"Handler modülü yüklenemedi: {module_name} - {e}")
        
        except ImportError as e:
            logger.error(f"Handler package bulunamadı: {package} - {e}")
        
        logger.info(f"Toplam {discovered} handler modülü keşfedildi")
        return discovered
    
    def _create_handler(self, config: HandlerConfig) -> Any:
        """Handler oluştur"""
        if config.handler_type == HandlerType.COMMAND:
            return CommandHandler(config.name, config.handler_func)
        
        elif config.handler_type == HandlerType.MESSAGE:
            return MessageHandler(config.filter_obj, config.handler_func)
        
        return None
    
    def _create_conversation_handler(
        self, 
        config: ConversationConfig
    ) -> ConversationHandler:
        """Conversation handler oluştur"""
        entry_points = [
            self._create_handler(h) for h in config.entry_points
        ]
        
        states = {}
        for state, handlers in config.states.items():
            states[state] = [self._create_handler(h) for h in handlers]
        
        fallbacks = [
            self._create_handler(h) for h in config.fallbacks
        ]
        
        return ConversationHandler(
            entry_points=entry_points,
            states=states,
            fallbacks=fallbacks,
        )
    
    def list_handlers(self) -> List[str]:
        """Kayıtlı handler isimlerini listele"""
        return [h.name for h in self._handlers]
    
    def clear(self) -> None:
        """Registry'yi temizle"""
        self._handlers.clear()
        self._conversations.clear()


# Global registry instance getter
def get_handler_registry() -> HandlerRegistry:
    """Handler Registry instance al"""
    return HandlerRegistry.get_instance()

