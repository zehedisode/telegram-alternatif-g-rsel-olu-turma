"""
Gemini CSS Selektörleri
Tüm CSS selektörleri merkezi olarak burada tanımlanır.
Değişiklik gerektiğinde sadece bu dosya güncellenir.
"""


class GeminiSelectors:
    """Gemini sayfası için CSS selektörleri"""
    
    # Prompt alanı
    PROMPT_AREA = 'div[role="textbox"][aria-label="Buraya istem girin"], .ql-editor'
    
    # Butonlar
    SEND_BUTTON = 'button.send-button, button[aria-label="Mesaj gönder"]'
    STOP_BUTTON = 'button[aria-label="Yanıtı durdur"]'
    COPY_BUTTON = 'button[aria-label="Kopyala"]'
    
    # Yanıt alanları - Birden fazla varyant
    MODEL_RESPONSE_VARIANTS = [
        'model-response',           # Tag name olarak
        '.model-response-text',     # Class olarak  
        '.response-content',
        '.message-content',
        '[data-message-author-role="model"]',
        '.markdown-content',
    ]
    MODEL_RESPONSE = 'model-response'  # Legacy uyumluluk
    THOUGHTS_BUTTON = 'button.thoughts-header-button'
    THOUGHTS_CONTENT = '.thoughts-content, .thinking-content'
    
    # Görsel butonları
    IMAGE_BUTTON = 'button.image-button img, .generated-image img'
    
    # Araçlar menüsü
    TOOLS_BUTTON_VARIANTS = [
        'button.toolbox-drawer-button',
        'button[class*="toolbox-drawer"]',
        'button.toolbox-drawer-button-with-label',
    ]
    
    IMAGE_GENERATION_OPTION = 'button.toolbox-drawer-item-list-button'
    OPTION_SELECTORS = [
        'button.toolbox-drawer-item-list-button',
        'button[class*="toolbox-drawer-item"]',
        '.mat-mdc-list-item button',
    ]
    
    # Yeni sohbet
    NEW_CHAT_VARIANTS = [
        'button[aria-label="Yeni sohbet"]',
        'button[aria-label="New chat"]',
        'button[class*="side-nav-action-"]',
        'a[href="/app"]',
    ]
    
    # Görsel yükleme doğrulama
    UPLOADED_IMAGE = 'img[src*="blob:"], img[src*="data:"], .uploaded-image, .image-preview'
    
    # İndirme butonları
    DOWNLOAD_BUTTONS = [
        'button[aria-label="Tam boyutlu resmi indir"]',
        'button[aria-label*="indir"]',
        'button[aria-label*="download"]',
    ]
    
    # Görsel URL tespiti
    GENERATED_IMAGE = 'img[src*="googleusercontent.com/gg/"]'

