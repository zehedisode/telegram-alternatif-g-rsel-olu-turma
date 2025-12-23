"""
Middleware Pipeline
Request/Response pipeline için middleware sistemi.
"""

import logging
from typing import Callable, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareContext:
    """Middleware context - request boyunca taşınan veri"""
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    data: dict = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class Middleware(ABC):
    """Base Middleware - yeni middleware eklemek için bu sınıftan türet"""
    
    @abstractmethod
    async def before(self, ctx: MiddlewareContext) -> bool:
        """Handler'dan önce çalışır. False dönerse pipeline durur."""
        return True
    
    async def after(self, ctx: MiddlewareContext, result: Any, error: Optional[Exception] = None) -> None:
        """Handler'dan sonra çalışır"""
        pass


class LoggingMiddleware(Middleware):
    """Logging middleware - tüm istekleri loglar"""
    
    async def before(self, ctx: MiddlewareContext) -> bool:
        user = ctx.update.effective_user
        chat = ctx.update.effective_chat
        logger.info(f"[REQUEST] User: {user.id if user else 'N/A'} | Chat: {chat.id if chat else 'N/A'}")
        return True
    
    async def after(self, ctx: MiddlewareContext, result: Any, error: Optional[Exception] = None) -> None:
        if error:
            logger.error(f"[RESPONSE] Error: {error}")
        else:
            logger.debug("[RESPONSE] Success")


class ErrorHandlingMiddleware(Middleware):
    """Merkezi hata yönetimi middleware"""
    
    def __init__(self, error_callback: Optional[Callable] = None):
        self.error_callback = error_callback
    
    async def before(self, ctx: MiddlewareContext) -> bool:
        return True
    
    async def after(self, ctx: MiddlewareContext, result: Any, error: Optional[Exception] = None) -> None:
        if error:
            logger.error(f"Handler hatası: {error}", exc_info=True)
            if ctx.update.message:
                try:
                    await ctx.update.message.reply_text("❌ Bir hata oluştu. Lütfen tekrar deneyin.")
                except Exception as e:
                    logger.error(f"Hata mesajı gönderilemedi: {e}")


class MiddlewarePipeline:
    """Middleware Pipeline - handler'ları middleware'lerle sarar"""
    
    def __init__(self):
        self._middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware) -> "MiddlewarePipeline":
        """Middleware ekle (fluent interface)"""
        self._middlewares.append(middleware)
        return self
    
    def wrap(self, handler: Callable) -> Callable:
        """Handler'ı middleware pipeline ile sar (decorator)"""
        @wraps(handler)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            ctx = MiddlewareContext(update=update, context=context)
            result, error = None, None
            
            # Before middlewares
            for middleware in self._middlewares:
                try:
                    if not await middleware.before(ctx):
                        return None
                except Exception as e:
                    error = e
                    break
            
            # Handler'ı çalıştır
            if not error:
                try:
                    result = await handler(update, context)
                except Exception as e:
                    error = e
            
            # After middlewares (ters sırada)
            for middleware in reversed(self._middlewares):
                try:
                    await middleware.after(ctx, result, error)
                except Exception as e:
                    logger.error(f"Middleware after hatası: {e}")
            
            return result
        return wrapped


def create_default_pipeline() -> MiddlewarePipeline:
    """Varsayılan middleware pipeline oluştur"""
    return MiddlewarePipeline().add(LoggingMiddleware()).add(ErrorHandlingMiddleware())
