"""
Core - Result Monad
Tip güvenli hata yönetimi için Result pattern implementasyonu.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Callable, Union

T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type
U = TypeVar('U')  # Transformed type


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    Result Monad - Fonksiyonel hata yönetimi.
    
    Exception fırlatmak yerine Result döndürerek:
    - Tip güvenliği sağlanır
    - Hata durumları açık olur
    - Composable kod yazılabilir
    
    Kullanım:
        def divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Result.fail("Sıfıra bölme hatası")
            return Result.ok(a / b)
        
        result = divide(10, 2)
        if result.is_ok:
            print(result.value)  # 5.0
    """
    
    _value: Optional[T] = None
    _error: Optional[E] = None
    _is_ok: bool = True
    
    @property
    def is_ok(self) -> bool:
        """Başarılı mı?"""
        return self._is_ok
    
    @property
    def is_error(self) -> bool:
        """Hatalı mı?"""
        return not self._is_ok
    
    @property
    def value(self) -> T:
        """
        Değeri al. Hata durumunda exception fırlatır.
        Önce is_ok kontrolü yapılmalı.
        """
        if not self._is_ok:
            raise ValueError(f"Result hata durumunda: {self._error}")
        return self._value  # type: ignore
    
    @property
    def error(self) -> E:
        """
        Hatayı al. Başarı durumunda exception fırlatır.
        Önce is_error kontrolü yapılmalı.
        """
        if self._is_ok:
            raise ValueError("Result başarı durumunda, hata yok")
        return self._error  # type: ignore
    
    @property
    def value_or_none(self) -> Optional[T]:
        """Değeri veya None döndür"""
        return self._value if self._is_ok else None
    
    @staticmethod
    def ok(value: T) -> Result[T, E]:
        """Başarılı Result oluştur"""
        return Result(_value=value, _is_ok=True)
    
    @staticmethod
    def fail(error: E) -> Result[T, E]:
        """Hatalı Result oluştur"""
        return Result(_error=error, _is_ok=False)
    
    def map(self, func: Callable[[T], U]) -> Result[U, E]:
        """
        Değeri dönüştür (başarı durumunda).
        
        Args:
            func: Dönüşüm fonksiyonu
            
        Returns:
            Dönüştürülmüş Result
        """
        if self._is_ok:
            try:
                return Result.ok(func(self._value))  # type: ignore
            except Exception as e:
                return Result.fail(e)  # type: ignore
        return Result.fail(self._error)  # type: ignore
    
    def flat_map(self, func: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """
        Değeri Result döndüren fonksiyonla dönüştür.
        
        Args:
            func: Result döndüren dönüşüm fonksiyonu
            
        Returns:
            Dönüştürülmüş Result
        """
        if self._is_ok:
            try:
                return func(self._value)  # type: ignore
            except Exception as e:
                return Result.fail(e)  # type: ignore
        return Result.fail(self._error)  # type: ignore
    
    def map_error(self, func: Callable[[E], E]) -> Result[T, E]:
        """
        Hatayı dönüştür (hata durumunda).
        """
        if not self._is_ok:
            return Result.fail(func(self._error))  # type: ignore
        return self
    
    def or_else(self, default: T) -> T:
        """Değeri veya varsayılan döndür"""
        return self._value if self._is_ok else default  # type: ignore
    
    def or_else_get(self, supplier: Callable[[], T]) -> T:
        """Değeri veya supplier'ın döndürdüğünü döndür"""
        return self._value if self._is_ok else supplier()  # type: ignore
    
    def on_success(self, action: Callable[[T], None]) -> Result[T, E]:
        """Başarı durumunda action çalıştır"""
        if self._is_ok:
            action(self._value)  # type: ignore
        return self
    
    def on_error(self, action: Callable[[E], None]) -> Result[T, E]:
        """Hata durumunda action çalıştır"""
        if not self._is_ok:
            action(self._error)  # type: ignore
        return self
    
    def __repr__(self) -> str:
        if self._is_ok:
            return f"Result.ok({self._value!r})"
        return f"Result.fail({self._error!r})"


def try_result(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """
    Exception'ı Result'a dönüştüren decorator.
    
    Kullanım:
        @try_result
        def risky_operation():
            return do_something_risky()
        
        result = risky_operation()
        if result.is_ok:
            print(result.value)
    """
    def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            return Result.ok(func(*args, **kwargs))
        except Exception as e:
            return Result.fail(e)
    return wrapper
