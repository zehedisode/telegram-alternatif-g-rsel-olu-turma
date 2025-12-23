"""
Core Module
Ortak altyapı bileşenleri.
"""

from .registry import PluginRegistry, PluginMetadata
from .result import Result, try_result
from .use_case_registry import UseCaseRegistry, UseCaseMetadata, get_use_case_registry

__all__ = [
    'PluginRegistry',
    'PluginMetadata',
    'Result',
    'try_result',
    'UseCaseRegistry',
    'UseCaseMetadata',
    'get_use_case_registry',
]

