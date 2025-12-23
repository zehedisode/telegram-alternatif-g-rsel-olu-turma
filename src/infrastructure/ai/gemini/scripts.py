"""
Gemini JavaScript Kodları
Tarayıcıda çalıştırılan JavaScript kodları
"""


class GeminiScripts:
    """Gemini sayfasında çalıştırılan JavaScript kodları"""
    
    # Görsel URL tespit scripti
    FIND_IMAGE_URL = """
        // Son model yanıtını bul
        const responses = document.querySelectorAll('model-response');
        if (responses.length === 0) return null;
        const lastResponse = responses[responses.length - 1];
        
        // 1. Strateji: Bilinen URL yapısı
        let imgs = lastResponse.querySelectorAll('img[src*="googleusercontent.com/gg/"]');
        
        // 2. Strateji: Fallback (boyut kontrolü)
        if (imgs.length === 0) {
            const allImgs = lastResponse.querySelectorAll('img');
            const validImgs = [];
            for (let img of allImgs) {
                if (img.naturalWidth > 300 && img.naturalHeight > 300) {
                    validImgs.push(img);
                }
            }
            if (validImgs.length > 0) {
                imgs = validImgs;
            }
        }

        if (imgs.length === 0) return null;
        
        // Yanıt içindeki en son görseli al
        const lastImg = imgs[imgs.length - 1];
        return lastImg.src;
    """
    
    # Prompt yazma scripti
    WRITE_PROMPT = """
        const editor = document.querySelector('.ql-editor p') || document.querySelector('.ql-editor');
        if (editor) {
            if (editor.tagName === 'P') {
                editor.innerText = arguments[0];
            } else {
                const p = document.createElement('p');
                p.innerText = arguments[0];
                editor.appendChild(p);
            }
            editor.dispatchEvent(new Event('input', { bubbles: true }));
        }
    """
    
    # Yüklenen görsel kontrolü
    CHECK_UPLOADED_IMAGE = """
        const imgs = document.querySelectorAll('img[src*="blob:"], img[src*="data:"], .uploaded-image, .image-preview');
        return imgs.length > 0;
    """
    
    # Yanıt metni alma (düşünme içeriği hariç)
    GET_RESPONSE_TEXT = """
        const response = arguments[0];
        const clone = response.cloneNode(true);
        
        // Düşünme sürecini göster butonunu kaldır
        const thoughtsButtons = clone.querySelectorAll('.thoughts-header-button, button.thoughts-header-button');
        thoughtsButtons.forEach(btn => btn.remove());
        
        // Düşünme içeriğini de kaldır (varsa)
        const thoughtsContent = clone.querySelectorAll('.thoughts-content, .thinking-content');
        thoughtsContent.forEach(content => content.remove());
        
        return clone.innerText.trim();
    """
    
    # User agent alma
    GET_USER_AGENT = "return navigator.userAgent;"
