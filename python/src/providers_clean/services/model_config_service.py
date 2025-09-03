"""Refactored model configuration service using repository pattern."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ..core.interfaces.unit_of_work import IUnitOfWork
from ..core.interfaces.repositories import IModelConfigRepository


class ModelConfig(BaseModel):
    """Configuration for a PydanticAI model."""
    service_name: str = Field(..., description="Name of the service (e.g., 'rag_agent')")
    model_string: str = Field(..., description="PydanticAI model string (e.g., 'openai:gpt-4o')")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for model generation")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens for generation")


class ModelConfigService:
    """Service for managing model configurations using repository pattern."""
    
    DEFAULT_MODELS = {
        "rag_agent": "openai:gpt-4o-mini",
        "document_agent": "anthropic:claude-3-haiku-20240307",
        "embeddings": "openai:text-embedding-3-small",
        "chat_agent": "openai:gpt-4o",
        "code_agent": "anthropic:claude-3-5-sonnet-20241022",
        "vision_agent": "openai:gpt-4o"
    }
    
    VALID_PROVIDERS = [
        "openai", "anthropic", "google", "groq", "mistral", 
        "cohere", "ai21", "replicate", "together", "fireworks",
        "openrouter", "deepseek", "xai", "ollama"
    ]
    
    def __init__(self, unit_of_work: IUnitOfWork):
        """Initialize service with Unit of Work.
        
        Args:
            unit_of_work: Unit of Work for managing repository operations
        """
        self.uow = unit_of_work
    
    async def get_model_config(self, service_name: str) -> ModelConfig:
        """Get model configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ModelConfig instance
        """
        async with self.uow:
            config = await self.uow.model_configs.get_config(service_name)
            
            if config:
                return ModelConfig(**config)
            
            # Return default configuration if not found
            default_model = self.DEFAULT_MODELS.get(service_name, "openai:gpt-4o-mini")
            return ModelConfig(
                service_name=service_name,
                model_string=default_model,
                temperature=0.7,
                max_tokens=None
            )
    
    async def set_model_config(
        self,
        service_name: str,
        model_string: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ModelConfig:
        """Set model configuration for a service.
        
        Args:
            service_name: Name of the service
            model_string: Model string (e.g., 'openai:gpt-4o')
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Updated ModelConfig
            
        Raises:
            ValueError: If model string is invalid
        """
        # Validate model string
        self.validate_model_string(model_string)
        
        config_data = {
            "model_string": model_string,
            "temperature": temperature or 0.7,
            "max_tokens": max_tokens
        }
        
        async with self.uow:
            saved_config = await self.uow.model_configs.save_config(service_name, config_data)
            await self.uow.commit()
            
            # saved_config already contains service_name, don't pass it again
            return ModelConfig(**saved_config)
    
    async def get_all_configs(self) -> Dict[str, str]:
        """Get all service configurations.
        
        Returns:
            Dictionary mapping service names to model strings
        """
        async with self.uow:
            configs = await self.uow.model_configs.get_all_configs()
            
            # Add defaults for any missing services
            for service, default_model in self.DEFAULT_MODELS.items():
                if service not in configs:
                    configs[service] = default_model
            
            return configs
    
    async def delete_config(self, service_name: str) -> bool:
        """Delete configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deleted, False if not found
        """
        async with self.uow:
            result = await self.uow.model_configs.delete_config(service_name)
            await self.uow.commit()
            return result
    
    def validate_model_string(self, model_string: str) -> bool:
        """Validate a model string format.
        
        Args:
            model_string: Model string to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If model string is invalid
        """
        if ':' not in model_string:
            raise ValueError(f"Invalid model string format: {model_string}. Expected format: 'provider:model'")
        
        provider = model_string.split(':', 1)[0]
        
        if provider not in self.VALID_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Valid providers: {', '.join(self.VALID_PROVIDERS)}")
        
        return True
    
    async def get_provider_from_service(self, service_name: str) -> str:
        """Get the provider for a service's current model.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Provider name
        """
        config = await self.get_model_config(service_name)
        provider = config.model_string.split(':', 1)[0]
        return provider
    
    async def bulk_update_provider(
        self,
        old_provider: str,
        new_provider: str,
        model_mappings: Optional[Dict[str, str]] = None
    ) -> int:
        """Update all services using a specific provider.
        
        Args:
            old_provider: Current provider to replace
            new_provider: New provider to use
            model_mappings: Optional specific model mappings
            
        Returns:
            Number of configurations updated
        """
        if model_mappings is None:
            model_mappings = {}
        
        async with self.uow:
            count = await self.uow.model_configs.bulk_update_provider(
                old_provider,
                new_provider,
                model_mappings
            )
            await self.uow.commit()
            return count