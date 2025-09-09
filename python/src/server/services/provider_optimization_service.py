"""
Provider Optimization Service

Handles provider-specific optimizations for embedding generation.
Supports all major embedding providers with equal priority.
"""

import logging
from typing import Dict, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)


class ProviderOptimizationService:
    """Manages provider-specific optimizations for embedding operations."""
    
    # Provider-specific API behavior configurations
    PROVIDER_CONFIGS = {
        "google": {
            "supports_dimensions": False,  # Google doesn't support dimensions parameter
            "api_format": "openai_compatible",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "default_dimensions": 768,
            "optimal_batch_size": 50,  # Conservative for Google API limits
            "cost_tier": "low"
        },
        "openai": {
            "supports_dimensions": True,   # OpenAI supports dimensions parameter
            "api_format": "native", 
            "base_url": None,  # Use default OpenAI API
            "default_dimensions": 1536,
            "optimal_batch_size": 100,  # OpenAI has generous rate limits
            "cost_tier": "medium"
        },
        "cohere": {
            "supports_dimensions": False,  # Cohere has fixed dimensions per model
            "api_format": "custom",
            "base_url": "https://api.cohere.ai/v1",
            "default_dimensions": 1024,
            "optimal_batch_size": 25,   # Cohere has stricter rate limits
            "cost_tier": "medium"
        },
        "mistral": {
            "supports_dimensions": True,   # Mistral supports dimensions in some models
            "api_format": "openai_compatible", 
            "base_url": "https://api.mistral.ai/v1",
            "default_dimensions": 1024,
            "optimal_batch_size": 75,
            "cost_tier": "medium"
        },
        "ollama": {
            "supports_dimensions": False,  # Ollama uses fixed model dimensions
            "api_format": "openai_compatible",
            "base_url": "http://host.docker.internal:11434/v1", 
            "default_dimensions": 768,
            "optimal_batch_size": 25,   # Local models may have memory constraints
            "cost_tier": "free"
        }
    }
    
    @classmethod
    async def get_provider_optimization(cls, service_name: str) -> Dict[str, Any]:
        """Get provider-specific optimization settings from database."""
        try:
            server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
            
            async with httpx.AsyncClient() as client:
                # Get model config for the service
                config_response = await client.get(
                    f"http://localhost:{server_port}/api/providers/models/config/{service_name}"
                )
                
                if config_response.status_code != 200:
                    raise ValueError(f"Failed to get model config for service {service_name}")
                
                model_config = config_response.json()
                model_string = model_config.get("model_string", "")
                
                if ":" not in model_string:
                    raise ValueError(f"Invalid model_string format: {model_string}")
                
                provider, model_id = model_string.split(":", 1)
                
                # Get provider config and merge with database settings
                provider_config = cls.PROVIDER_CONFIGS.get(provider, {})
                
                # Database values override defaults
                optimization = {
                    "provider": provider,
                    "model_id": model_id, 
                    "model_string": model_string,
                    "embedding_dimensions": model_config.get("embedding_dimensions") or provider_config.get("default_dimensions"),
                    "batch_size": model_config.get("optimal_batch_size") or model_config.get("batch_size") or provider_config.get("optimal_batch_size", 100),
                    "supports_dimensions": provider_config.get("supports_dimensions", True),
                    "base_url": provider_config.get("base_url"),
                    "cost_per_million": model_config.get("cost_per_million_tokens") or provider_config.get("cost_tier"),
                    "max_input_tokens": model_config.get("max_input_tokens") or provider_config.get("max_input_tokens", 8000)
                }
                
                logger.info(f"Provider optimization for {service_name}: {provider} with {optimization['embedding_dimensions']} dimensions")
                return optimization
                
        except Exception as e:
            logger.error(f"Failed to get provider optimization for {service_name}: {e}")
            # Return safe defaults
            return {
                "provider": "openai",
                "model_id": "text-embedding-ada-002", 
                "model_string": "openai:text-embedding-ada-002",
                "embedding_dimensions": 1536,
                "batch_size": 100,
                "supports_dimensions": True,
                "base_url": None,
                "cost_per_million": "medium",
                "max_input_tokens": 8000
            }
    
    @classmethod
    def get_supported_dimensions(cls) -> list[int]:
        """Get all supported embedding dimensions across all providers."""
        return [384, 768, 1024, 1536, 3072]
    
    @classmethod
    def get_providers_for_dimension(cls, dimension: int) -> list[str]:
        """Get providers that support a specific dimension."""
        provider_dims = {
            384: ["cohere", "ollama"],      # Cohere light, Ollama all-minilm
            768: ["google", "ollama"],      # Google, Ollama nomic-embed
            1024: ["cohere", "mistral", "ollama"],  # Cohere standard, Mistral, Ollama mxbai
            1536: ["openai"],               # OpenAI small/ada-002
            3072: ["openai"]                # OpenAI large
        }
        return provider_dims.get(dimension, [])
    
    @classmethod
    async def get_cost_optimal_provider(cls, target_dimension: int) -> Optional[str]:
        """Get the most cost-effective provider for a given dimension."""
        providers = cls.get_providers_for_dimension(target_dimension)
        
        # Cost preference order (lower cost preferred)
        cost_order = {
            "ollama": 0,    # Free (local)
            "google": 1,    # Low cost
            "openai": 2,    # Medium cost  
            "cohere": 3,    # Medium cost
            "mistral": 3    # Medium cost
        }
        
        if not providers:
            return None
            
        # Return lowest cost provider for this dimension
        return min(providers, key=lambda p: cost_order.get(p, 999))
    
    @classmethod
    def should_use_dimensions_param(cls, provider: str, model_config: Dict[str, Any]) -> bool:
        """Determine if dimensions parameter should be used for this provider."""
        # Check database setting first
        if "supports_dimensions_param" in model_config:
            return model_config["supports_dimensions_param"]
        
        # Fall back to provider defaults
        provider_config = cls.PROVIDER_CONFIGS.get(provider, {})
        return provider_config.get("supports_dimensions", True)