"""
Retry Utility
Merkezi retry/wait mekanizması - DRY prensibi
"""

import time
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Retry yapılandırması"""
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_DELAY = 1.0
    DEFAULT_BACKOFF = 2.0
    DEFAULT_MAX_DELAY = 30.0


def wait_with_retry(
    condition_fn: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 1.0,
    description: str = "condition"
) -> bool:
    """
    Koşul sağlanana kadar bekle.
    
    Args:
        condition_fn: True döndüğünde bekleyişi sonlandıran fonksiyon
        timeout: Maksimum bekleme süresi (saniye)
        interval: Kontrol aralığı (saniye)
        description: Log mesajları için açıklama
    
    Returns:
        True eğer koşul sağlandıysa, False eğer timeout olduysa
    """
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            if condition_fn():
                logger.debug(f"{description} sağlandı (deneme {attempt})")
                return True
        except Exception as e:
            logger.debug(f"{description} kontrol hatası: {e}")
        
        time.sleep(interval)
    
    logger.warning(f"{description} timeout ({timeout}s)")
    return False


def retry_on_exception(
    max_attempts: int = RetryConfig.DEFAULT_MAX_ATTEMPTS,
    delay: float = RetryConfig.DEFAULT_DELAY,
    backoff: float = RetryConfig.DEFAULT_BACKOFF,
    max_delay: float = RetryConfig.DEFAULT_MAX_DELAY,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator: Hata durumunda yeniden dene.
    
    Args:
        max_attempts: Maksimum deneme sayısı
        delay: İlk bekleme süresi (saniye)
        backoff: Her denemede çarpan
        max_delay: Maksimum bekleme süresi
        exceptions: Yakalanacak exception türleri
        on_retry: Her retry'da çağrılacak callback
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} başarısız (deneme {attempt}/{max_attempts}): {e}"
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(min(current_delay, max_delay))
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} tüm denemeler başarısız: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def safe_wait(seconds: float, description: str = "") -> None:
    """
    Güvenli bekleme - loglama ile.
    
    Args:
        seconds: Bekleme süresi
        description: Log için açıklama
    """
    if description:
        logger.debug(f"{description} için {seconds}s bekleniyor...")
    time.sleep(seconds)
