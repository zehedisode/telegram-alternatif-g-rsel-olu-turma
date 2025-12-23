"""
Core Module Tests
Result monad ve plugin registry testleri
"""

import pytest
from src.core import Result, PluginMetadata


class TestResult:
    """Result monad testleri"""
    
    def test_ok_result(self):
        """Başarılı result oluşturma"""
        result = Result.ok(42)
        
        assert result.is_ok
        assert not result.is_error
        assert result.value == 42
    
    def test_fail_result(self):
        """Hatalı result oluşturma"""
        result = Result.fail("Hata mesajı")
        
        assert result.is_error
        assert not result.is_ok
        assert result.error == "Hata mesajı"
    
    def test_value_on_error_raises(self):
        """Hatalı result'ta value erişimi hata fırlatmalı"""
        result = Result.fail("Hata")
        
        with pytest.raises(ValueError):
            _ = result.value
    
    def test_error_on_ok_raises(self):
        """Başarılı result'ta error erişimi hata fırlatmalı"""
        result = Result.ok(10)
        
        with pytest.raises(ValueError):
            _ = result.error
    
    def test_map_on_ok(self):
        """Başarılı result'ta map çalışmalı"""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_ok
        assert mapped.value == 10
    
    def test_map_on_error(self):
        """Hatalı result'ta map hatayı korumalı"""
        result = Result.fail("Hata")
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_error
        assert mapped.error == "Hata"
    
    def test_or_else(self):
        """or_else varsayılan değer döndürmeli"""
        ok_result = Result.ok(42)
        fail_result = Result.fail("Hata")
        
        assert ok_result.or_else(0) == 42
        assert fail_result.or_else(0) == 0
    
    def test_value_or_none(self):
        """value_or_none hata durumunda None döndürmeli"""
        ok_result = Result.ok(42)
        fail_result = Result.fail("Hata")
        
        assert ok_result.value_or_none == 42
        assert fail_result.value_or_none is None


class TestPluginMetadata:
    """PluginMetadata testleri"""
    
    def test_create_metadata(self):
        """Metadata oluşturma"""
        meta = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            supported_features={"feature1", "feature2"},
            priority=5
        )
        
        assert meta.name == "test_plugin"
        assert meta.version == "1.0.0"
        assert meta.priority == 5
    
    def test_supports_feature(self):
        """Özellik desteği kontrolü"""
        meta = PluginMetadata(
            name="test",
            supported_features={"analyze", "generate"}
        )
        
        assert meta.supports("analyze")
        assert meta.supports("generate")
        assert not meta.supports("unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
