"""
Merkezi Loglama Modülü
Tüm modüller için tek noktadan loglama yapılandırması
"""

import logging
import sys
from pathlib import Path


# Log formatları
CONSOLE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s"
FILE_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Path = None
) -> logging.Logger:
    """
    Logger oluştur ve yapılandır.
    
    Args:
        name: Logger adı (genellikle __name__)
        level: Log seviyesi
        log_file: Opsiyonel log dosyası yolu
    
    Returns:
        Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    
    # Eğer handler zaten eklenmiş ise tekrar ekleme
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Konsol handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # Dosya handler (opsiyonel)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Mevcut veya yeni logger al.
    
    Args:
        name: Logger adı
    
    Returns:
        Logger instance
    """
    return setup_logger(name)
