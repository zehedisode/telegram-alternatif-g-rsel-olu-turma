"""
Use Case Registry Tests
Registry ve auto-discovery testleri
"""

import pytest
from pathlib import Path
import sys

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import UseCaseRegistry, UseCaseMetadata, get_use_case_registry


class TestUseCaseMetadata:
    """UseCaseMetadata testleri"""
    
    def test_create_metadata(self):
        """Metadata oluşturma"""
        meta = UseCaseMetadata(
            name="test_use_case",
            version="1.0.0",
            description="Test use case",
            requires_browser=True,
            requires_ai=True,
        )
        
        assert meta.name == "test_use_case"
        assert meta.version == "1.0.0"
        assert meta.requires_browser is True
        assert meta.requires_ai is True
    
    def test_default_values(self):
        """Varsayılan değerler"""
        meta = UseCaseMetadata(name="simple")
        
        assert meta.version == "1.0.0"
        assert meta.requires_browser is False
        assert meta.requires_ai is False
        assert meta.is_async is True


class TestUseCaseRegistry:
    """UseCaseRegistry testleri"""
    
    def setup_method(self):
        """Test öncesi registry'yi temizle"""
        UseCaseRegistry.reset()
    
    def teardown_method(self):
        """Test sonrası registry'yi temizle"""
        UseCaseRegistry.reset()
    
    def test_singleton(self):
        """Singleton pattern testi"""
        registry1 = get_use_case_registry()
        registry2 = get_use_case_registry()
        
        assert registry1 is registry2
    
    def test_reset(self):
        """Reset fonksiyonu"""
        registry1 = get_use_case_registry()
        UseCaseRegistry.reset()
        registry2 = get_use_case_registry()
        
        assert registry1 is not registry2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
