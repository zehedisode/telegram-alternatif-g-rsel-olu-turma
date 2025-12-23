"""
Dependency Injection Container - Refactored
ContainerBuilder pattern ile OCP uyumlu DI yönetimi.
"""

from typing import Optional, Dict, Any, Type
import logging

from .infrastructure import (
    SeleniumBrowserService,
    GeminiAIService,
    TelegramBotGateway,
    ConfigService,
)
from .infrastructure.ai.providers import (
    BaseAIProvider,
    AIProviderRegistry,
    GeminiProvider,
    get_ai_registry,
)
from .application import (
    ProcessImageWorkflowUseCase,
    AnalyzeImageUseCase,
    GenerateImageUseCase,
    WorkflowStrategy,
    AnalyzeAndGenerateStrategy,
    DirectGenerateStrategy,
)
from .core import get_use_case_registry, UseCaseRegistry
from .domain import IConfigProvider

logger = logging.getLogger(__name__)


class ContainerBuilder:
    """
    Container Builder - OCP Uyumlu.
    
    Fluent interface ile container konfigürasyonu:
    
        container = (ContainerBuilder()
            .with_config(ConfigService())
            .with_ai_provider("gemini")
            .with_workflow_strategy("analyze_and_generate")
            .build())
    """
    
    def __init__(self):
        self._config: Optional[IConfigProvider] = None
        self._ai_provider_name: str = "gemini"
        self._workflow_strategy_name: str = "analyze_and_generate"
        self._custom_providers: Dict[str, Type[BaseAIProvider]] = {}
        self._custom_strategies: Dict[str, Type[WorkflowStrategy]] = {}
    
    def with_config(self, config: IConfigProvider) -> "ContainerBuilder":
        """Konfigürasyon sağlayıcısı belirle"""
        self._config = config
        return self
    
    def with_ai_provider(self, provider_name: str) -> "ContainerBuilder":
        """AI provider adını belirle"""
        self._ai_provider_name = provider_name
        return self
    
    def with_workflow_strategy(self, strategy_name: str) -> "ContainerBuilder":
        """Workflow strategy adını belirle"""
        self._workflow_strategy_name = strategy_name
        return self
    
    def register_provider(
        self, 
        provider_class: Type[BaseAIProvider]
    ) -> "ContainerBuilder":
        """Custom provider kaydet"""
        meta = provider_class.get_metadata()
        self._custom_providers[meta.name] = provider_class
        return self
    
    def register_workflow_strategy(
        self,
        strategy_class: Type[WorkflowStrategy]
    ) -> "ContainerBuilder":
        """Custom workflow strategy kaydet"""
        name = strategy_class.get_name()
        self._custom_strategies[name] = strategy_class
        return self
    
    def build(self) -> "Container":
        """Container oluştur"""
        return Container(
            config=self._config,
            ai_provider_name=self._ai_provider_name,
            workflow_strategy_name=self._workflow_strategy_name,
            custom_providers=self._custom_providers,
            custom_strategies=self._custom_strategies,
        )


class Container:
    """
    Dependency Injection Container.
    Clean Architecture bağımlılık yönetimi.
    
    OCP: Yeni servis = yeni provider/strategy, Container değişikliği yok.
    """
    
    _instance: Optional["Container"] = None
    
    def __init__(
        self,
        config: Optional[IConfigProvider] = None,
        ai_provider_name: str = "gemini",
        workflow_strategy_name: str = "analyze_and_generate",
        custom_providers: Optional[Dict[str, Type[BaseAIProvider]]] = None,
        custom_strategies: Optional[Dict[str, Type[WorkflowStrategy]]] = None,
    ):
        logger.info("DI Container başlatılıyor...")
        
        # 1. Config
        self.config = config or ConfigService()
        
        # 2. Infrastructure - Browser
        self.browser_service = SeleniumBrowserService(
            profile_path=self.config.chrome_profile_path,
            download_dir=self.config.images_dir
        )
        
        # 3. AI Provider Registry
        self._setup_ai_registry(custom_providers)
        
        # 4. AI Service - Registry'den al
        self.ai_provider = self._create_ai_provider(ai_provider_name)
        
        # 5. Legacy uyumluluk için ai_service alias
        self.ai_service = GeminiAIService(
            browser_service=self.browser_service,
            gemini_url=self.config.gemini_url,
            download_dir=self.config.images_dir
        )
        
        # 6. Bot Gateway
        self.bot_gateway = TelegramBotGateway(
            token=self.config.bot_token
        )
        
        # 7. Workflow Strategy Registry
        self._workflow_strategies: Dict[str, WorkflowStrategy] = {}
        self._setup_workflow_strategies(custom_strategies)
        self._active_strategy_name = workflow_strategy_name
        
        # 8. Use Case Registry
        self._use_case_registry = get_use_case_registry()
        
        # 9. Application Use Cases (legacy uyumluluk)
        self.analyze_image_use_case = AnalyzeImageUseCase(
            ai_service=self.ai_service,
            browser_service=self.browser_service,
        )
        
        self.generate_image_use_case = GenerateImageUseCase(
            ai_service=self.ai_service,
        )
        
        self.process_workflow_use_case = ProcessImageWorkflowUseCase(
            ai_service=self.ai_service,
            browser_service=self.browser_service,
            bot_gateway=self.bot_gateway,
        )
        
        logger.info("DI Container hazır")
    
    def _setup_ai_registry(
        self, 
        custom_providers: Optional[Dict[str, Type[BaseAIProvider]]]
    ) -> None:
        """AI Provider Registry'yi kur"""
        registry = get_ai_registry()
        
        # Varsayılan provider'ı kaydet
        registry.register(GeminiProvider)
        
        # Custom provider'ları kaydet
        if custom_providers:
            for provider_class in custom_providers.values():
                registry.register(provider_class)
    
    def _setup_workflow_strategies(
        self,
        custom_strategies: Optional[Dict[str, Type[WorkflowStrategy]]]
    ) -> None:
        """Workflow strategy'leri kur"""
        # Varsayılan stratejileri kaydet
        self._register_strategy(AnalyzeAndGenerateStrategy(
            ai_service=self.ai_service,
            browser_service=self.browser_service,
        ))
        self._register_strategy(DirectGenerateStrategy(
            ai_service=self.ai_service,
            browser_service=self.browser_service,
        ))
        
        # Custom stratejileri kaydet
        if custom_strategies:
            for strategy_class in custom_strategies.values():
                instance = strategy_class(
                    ai_service=self.ai_service,
                    browser_service=self.browser_service,
                )
                self._register_strategy(instance)
    
    def _register_strategy(self, strategy: WorkflowStrategy) -> None:
        """Strateji kaydet"""
        name = strategy.get_name()
        self._workflow_strategies[name] = strategy
        logger.debug(f"Workflow strategy kaydedildi: {name}")
    
    def _create_ai_provider(self, provider_name: str) -> BaseAIProvider:
        """AI Provider oluştur"""
        registry = get_ai_registry()
        
        return registry.get(
            provider_name,
            browser_service=self.browser_service,
            gemini_url=self.config.gemini_url,
            download_dir=self.config.images_dir,
        )
    
    def get_workflow_strategy(self, name: Optional[str] = None) -> WorkflowStrategy:
        """
        Workflow strategy al.
        
        Args:
            name: Strategy adı (None ise aktif strateji)
            
        Returns:
            WorkflowStrategy instance
            
        Raises:
            KeyError: Strateji bulunamadığında
        """
        strategy_name = name or self._active_strategy_name
        
        if strategy_name not in self._workflow_strategies:
            available = list(self._workflow_strategies.keys())
            raise KeyError(f"Strategy bulunamadı: '{strategy_name}'. Mevcut: {available}")
        
        return self._workflow_strategies[strategy_name]
    
    def list_workflow_strategies(self) -> list:
        """Mevcut stratejileri listele"""
        return list(self._workflow_strategies.keys())
    
    @property
    def use_case_registry(self) -> UseCaseRegistry:
        """Use case registry'e erişim"""
        return self._use_case_registry
    
    @classmethod
    def get_instance(cls) -> "Container":
        """Singleton instance döndür"""
        if cls._instance is None:
            cls._instance = ContainerBuilder().build()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Container'ı sıfırla (test için)"""
        if cls._instance:
            cls._instance.cleanup()
        cls._instance = None
        AIProviderRegistry.reset()
        UseCaseRegistry.reset()
    
    def cleanup(self):
        """Kaynakları temizle"""
        if self.browser_service.is_running():
            self.browser_service.stop()


# Global container instance (lazy)
def get_container() -> Container:
    """Container instance al"""
    return Container.get_instance()

