"""
Gemini Timeout Sabitleri
Merkezi timeout yönetimi - DRY prensibi
"""


class GeminiTimeouts:
    """Gemini işlemleri için timeout değerleri"""
    
    # Sayfa navigasyonu
    PAGE_LOAD = 5
    PAGE_READY = 3
    
    # Element bekleme
    ELEMENT_VISIBLE = 30
    ELEMENT_CLICKABLE = 20
    BUTTON_CLICK = 15
    
    # Görsel işlemleri
    IMAGE_UPLOAD = 5
    IMAGE_VERIFY = 10
    IMAGE_GENERATION = 180
    
    # Yanıt bekleme
    RESPONSE_WAIT = 120
    RESPONSE_CHECK = 3
    
    # Clipboard
    CLIPBOARD_WAIT = 2
    
    # Genel aralıklar
    SHORT_WAIT = 1
    MEDIUM_WAIT = 2
    LONG_WAIT = 5
