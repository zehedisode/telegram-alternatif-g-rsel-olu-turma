"""
Domain Entity Tests
ImageEntity ve ProcessContext için birim testleri
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.domain.entities import (
    ImageEntity,
    ProcessContext,
    SessionEntity,
    ProcessStatus,

)
from src.domain.value_objects import Prompt, ImageCount


class TestImageEntity:
    """ImageEntity birim testleri"""
    
    def test_create_image_entity(self):
        """ImageEntity oluşturma"""
        entity = ImageEntity(path="/tmp/test.png")
        
        assert entity.path == "/tmp/test.png"
        assert entity.id is not None
        assert len(entity.id) == 8
        assert isinstance(entity.created_at, datetime)
    
    def test_filename_property(self):
        """Dosya adı özelliği"""
        entity = ImageEntity(path="/home/user/images/photo.jpg")
        
        assert entity.filename == "photo.jpg"
    
    def test_extension_property(self):
        """Uzantı özelliği"""
        entity = ImageEntity(path="/tmp/image.PNG")
        
        assert entity.extension == ".png"
    
    def test_is_valid_image(self):
        """Geçerli görsel formatı kontrolü"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        
        for ext in valid_extensions:
            entity = ImageEntity(path=f"/tmp/test{ext}")
            assert entity.is_valid_image(), f"{ext} geçerli olmalı"
        
        invalid_entity = ImageEntity(path="/tmp/test.txt")
        assert not invalid_entity.is_valid_image()
    
    def test_exists_property(self):
        """Dosya varlık kontrolü"""
        # Var olmayan dosya
        entity = ImageEntity(path="/nonexistent/path.png")
        assert not entity.exists
        
        # Geçici dosya ile test
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
        
        try:
            entity = ImageEntity(path=temp_path)
            assert entity.exists
        finally:
            os.unlink(temp_path)


class TestProcessContext:
    """ProcessContext birim testleri"""
    
    def test_create_context(self):
        """ProcessContext oluşturma"""
        session = SessionEntity(chat_id="123", user_id="456")
        image = ImageEntity(path="/tmp/test.png")
        
        context = ProcessContext(
            session=session,
            original_image=image,
            target_count=3,
        )
        
        assert context.status == ProcessStatus.PENDING
        assert context.target_count == 3
        assert len(context.generated_images) == 0
    
    def test_mark_completed(self):
        """Tamamlandı işareti"""
        session = SessionEntity()
        image = ImageEntity(path="/tmp/test.png")
        context = ProcessContext(session=session, original_image=image, target_count=1)
        
        context.mark_completed()
        
        assert context.is_completed
        assert context.completed_at is not None
    
    def test_mark_failed(self):
        """Başarısız işareti"""
        session = SessionEntity()
        image = ImageEntity(path="/tmp/test.png")
        context = ProcessContext(session=session, original_image=image, target_count=1)
        
        context.mark_failed("Test hatası")
        
        assert context.is_failed
        assert context.error_message == "Test hatası"
    
    def test_add_generated_image(self):
        """Oluşturulan görsel ekleme"""
        session = SessionEntity()
        image = ImageEntity(path="/tmp/test.png")
        context = ProcessContext(session=session, original_image=image, target_count=3)
        
        context.add_generated_image(ImageEntity(path="/tmp/gen1.png"))
        context.add_generated_image(ImageEntity(path="/tmp/gen2.png"))
        
        assert context.completed_count == 2
        assert context.progress_percentage == pytest.approx(66.67, rel=0.01)


class TestPrompt:
    """Prompt Value Object testleri"""
    
    def test_create_prompt(self):
        """Prompt oluşturma"""
        prompt = Prompt(text="Test prompt")
        
        assert str(prompt) == "Test prompt"
        assert len(prompt) == 11
    
    def test_empty_prompt_raises(self):
        """Boş prompt hata fırlatmalı"""
        with pytest.raises(ValueError):
            Prompt(text="")
        
        with pytest.raises(ValueError):
            Prompt(text="   ")
    
    def test_create_method(self):
        """Güvenli oluşturma metodu"""
        assert Prompt.create(None) is None
        assert Prompt.create("") is None
        assert Prompt.create("  ") is None
        
        prompt = Prompt.create("Valid prompt")
        assert prompt is not None
        assert str(prompt) == "Valid prompt"
    
    def test_truncate(self):
        """Kısaltma metodu"""
        prompt = Prompt(text="Bu çok uzun bir prompt metnidir")
        truncated = prompt.truncate(10)
        
        assert len(truncated) == 10
        assert str(truncated) == "Bu çok uzu"


class TestImageCount:
    """ImageCount Value Object testleri"""
    
    def test_create_image_count(self):
        """ImageCount oluşturma"""
        count = ImageCount(value=5)
        
        assert int(count) == 5
    
    def test_invalid_count_raises(self):
        """Geçersiz sayı hata fırlatmalı"""
        with pytest.raises(ValueError):
            ImageCount(value=0)
        
        with pytest.raises(ValueError):
            ImageCount(value=10)  # Max 9
        
        with pytest.raises(ValueError):
            ImageCount(value=-1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
