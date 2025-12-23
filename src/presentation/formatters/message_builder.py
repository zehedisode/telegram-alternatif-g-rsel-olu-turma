"""
Message Builder
Mesaj formatlamaları için yardımcı sınıf
"""


class MessageBuilder:
    """
    Telegram mesajları için builder.
    Tutarlı formatlama sağlar.
    """
    
    SEPARATOR = "━" * 24
    
    @classmethod
    def success(cls, title: str, body: str = "", footer: str = "") -> str:
        """Başarı mesajı oluştur"""
        lines = [f"🎉 **{title}**", cls.SEPARATOR, ""]
        if body:
            lines.append(body)
            lines.append("")
        if footer:
            lines.append(footer)
        return "\n".join(lines)
    
    @classmethod
    def error(cls, title: str, details: str = "", suggestion: str = "") -> str:
        """Hata mesajı oluştur"""
        lines = [f"❌ **{title}**", cls.SEPARATOR, ""]
        if details:
            lines.append(f"⚠️ {details}")
            lines.append("")
        if suggestion:
            lines.append(f"💡 {suggestion}")
        return "\n".join(lines)
    
    @classmethod
    def info(cls, title: str, items: list = None) -> str:
        """Bilgi mesajı oluştur"""
        lines = [f"📊 **{title}**", cls.SEPARATOR, ""]
        if items:
            for item in items:
                lines.append(item)
        return "\n".join(lines)
    
    @classmethod
    def progress(
        cls,
        title: str,
        steps: list,
        current_step: int,
        extra_info: str = "",
        elapsed_seconds: int = 0,
    ) -> str:
        """İlerleme mesajı oluştur"""
        lines = [f"🤖 **{title}**", cls.SEPARATOR]
        
        for i, step in enumerate(steps):
            if i < current_step:
                lines.append(f"✅ ~~{step}~~")
            elif i == current_step:
                lines.append(f"▶️ **{step}...**")
            else:
                lines.append(f"⬜ {step}")
        
        if extra_info:
            lines.append("")
            lines.append(f"💡 _{extra_info}_")
        
        if elapsed_seconds > 0:
            lines.append("")
            lines.append(f"⏱️ Geçen süre: {elapsed_seconds}s")
        
        return "\n".join(lines)
