"""
Workflow Strategy Tests
Strategy pattern ve workflow orkestrasyon testleri
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path
import sys

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.application.strategies import (
    WorkflowStrategy,
    WorkflowContext,
    AnalyzeAndGenerateStrategy,
    DirectGenerateStrategy,
)
from src.application.dtos import ImageProcessRequest, ImageProcessResult
from src.domain import ImageEntity, SessionEntity, ProcessStatus


class TestWorkflowContext:
    """WorkflowContext testleri"""
    
    def test_create_context(self):
        """Context oluşturma"""
        request = ImageProcessRequest(
            chat_id="123",
            user_id="456",
            image_path="/tmp/test.jpg",
            target_count=3,
        )
        session = SessionEntity(chat_id="123")
        image = ImageEntity(path="/tmp/test.jpg")
        
        context = WorkflowContext(
            request=request,
            session=session,
            original_image=image,
            system_prompt="Test prompt",
        )
        
        assert context.request.chat_id == "123"
        assert context.completed_count == 0
        assert context.extracted_prompt is None
    
    def test_add_generated_image(self):
        """Oluşturulan görsel ekleme"""
        request = ImageProcessRequest(
            chat_id="123",
            user_id="456",
            image_path="/tmp/test.jpg",
            target_count=2,
        )
        context = WorkflowContext(
            request=request,
            session=SessionEntity(),
            original_image=ImageEntity(path="/tmp/test.jpg"),
            system_prompt="Test prompt",
        )
        
        context.add_generated_image(ImageEntity(path="/tmp/gen1.png"))
        context.add_generated_image(ImageEntity(path="/tmp/gen2.png"))
        
        assert context.completed_count == 2
        assert len(context.generated_images) == 2


class TestAnalyzeAndGenerateStrategy:
    """AnalyzeAndGenerateStrategy testleri"""
    
    def test_get_name(self):
        """Strategy adı doğrulaması"""
        assert AnalyzeAndGenerateStrategy.get_name() == "analyze_and_generate"
    
    def test_get_description(self):
        """Strategy açıklaması"""
        desc = AnalyzeAndGenerateStrategy.get_description()
        assert len(desc) > 0
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Başarılı akış testi"""
        # Mock servisler
        ai_service = MagicMock()
        ai_service.analyze_image.return_value = "Extracted prompt"
        ai_service.generate_image.return_value = ImageEntity(path="/tmp/gen.png")
        
        browser_service = MagicMock()
        browser_service.is_running.return_value = False
        
        strategy = AnalyzeAndGenerateStrategy(
            ai_service=ai_service,
            browser_service=browser_service,
        )
        
        request = ImageProcessRequest(
            chat_id="123",
            user_id="456",
            image_path="/tmp/test.jpg",
            target_count=1,
        )
        
        context = WorkflowContext(
            request=request,
            session=SessionEntity(),
            original_image=ImageEntity(path="/tmp/test.jpg"),
            system_prompt="Analyze this image",
        )
        
        result = await strategy.execute(context)
        
        assert result.success
        assert len(result.generated_image_paths) == 1
        assert result.extracted_prompt == "Extracted prompt"
        
        # Servis çağrıları doğrulaması
        browser_service.start.assert_called_once()
        ai_service.analyze_image.assert_called_once()
        ai_service.generate_image.assert_called_once()


class TestDirectGenerateStrategy:
    """DirectGenerateStrategy testleri"""
    
    def test_get_name(self):
        """Strategy adı doğrulaması"""
        assert DirectGenerateStrategy.get_name() == "direct_generate"
    
    @pytest.mark.asyncio
    async def test_execute_without_prompt_fails(self):
        """Prompt olmadan başarısız olmalı"""
        ai_service = MagicMock()
        browser_service = MagicMock()
        
        strategy = DirectGenerateStrategy(
            ai_service=ai_service,
            browser_service=browser_service,
        )
        
        request = ImageProcessRequest(
            chat_id="123",
            user_id="456",
            image_path="/tmp/test.jpg",
            target_count=1,
        )
        
        context = WorkflowContext(
            request=request,
            session=SessionEntity(),
            original_image=ImageEntity(path="/tmp/test.jpg"),
            system_prompt="",  # Boş prompt
        )
        
        result = await strategy.execute(context)
        
        assert not result.success
        assert "prompt gerekli" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Başarılı akış testi"""
        ai_service = MagicMock()
        ai_service.generate_image.return_value = ImageEntity(path="/tmp/gen.png")
        
        browser_service = MagicMock()
        browser_service.is_running.return_value = True
        
        strategy = DirectGenerateStrategy(
            ai_service=ai_service,
            browser_service=browser_service,
        )
        
        request = ImageProcessRequest(
            chat_id="123",
            user_id="456",
            image_path="/tmp/test.jpg",
            target_count=2,
        )
        
        context = WorkflowContext(
            request=request,
            session=SessionEntity(),
            original_image=ImageEntity(path="/tmp/test.jpg"),
            system_prompt="Generate a beautiful image",
        )
        
        result = await strategy.execute(context)
        
        assert result.success
        assert len(result.generated_image_paths) == 2
        assert ai_service.generate_image.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
