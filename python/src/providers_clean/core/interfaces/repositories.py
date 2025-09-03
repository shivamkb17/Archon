"""Repository interfaces for the provider system.

These interfaces define the contract for data access operations,
enabling dependency inversion and improving testability.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class IModelConfigRepository(ABC):
    """Repository interface for model configuration operations."""
    
    @abstractmethod
    async def get_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration for a service.
        
        Args:
            service_name: Name of the service (e.g., 'rag_agent')
            
        Returns:
            Configuration dict or None if not found
        """
        pass
    
    @abstractmethod
    async def save_config(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update model configuration for a service.
        
        Args:
            service_name: Name of the service
            config: Configuration dictionary containing model_string, temperature, etc.
            
        Returns:
            Saved configuration dictionary
        """
        pass
    
    @abstractmethod
    async def get_all_configs(self) -> Dict[str, str]:
        """Get all service configurations.
        
        Returns:
            Dictionary mapping service names to model strings
        """
        pass
    
    @abstractmethod
    async def delete_config(self, service_name: str) -> bool:
        """Delete configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def bulk_update_provider(self, old_provider: str, new_provider: str, new_models: Dict[str, str]) -> int:
        """Update all configurations using a specific provider.
        
        Args:
            old_provider: Current provider name
            new_provider: New provider name
            new_models: Mapping of old model strings to new ones
            
        Returns:
            Number of configurations updated
        """
        pass


class IApiKeyRepository(ABC):
    """Repository interface for API key management."""
    
    @abstractmethod
    async def store_key(self, provider: str, encrypted_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store an encrypted API key for a provider.
        
        Args:
            provider: Provider name (e.g., 'openai')
            encrypted_key: Encrypted API key
            metadata: Optional metadata (base_url, etc.)
            
        Returns:
            True if stored successfully
        """
        pass
    
    @abstractmethod
    async def get_key(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get encrypted API key and metadata for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary with encrypted_key and metadata, or None if not found
        """
        pass
    
    @abstractmethod
    async def get_active_providers(self) -> List[str]:
        """Get list of providers with active API keys.
        
        Returns:
            List of provider names
        """
        pass
    
    @abstractmethod
    async def deactivate_key(self, provider: str) -> bool:
        """Deactivate (soft delete) an API key.
        
        Args:
            provider: Provider name
            
        Returns:
            True if deactivated, False if not found
        """
        pass
    
    @abstractmethod
    async def rotate_key(self, provider: str, new_encrypted_key: str) -> bool:
        """Rotate an API key for a provider.
        
        Args:
            provider: Provider name
            new_encrypted_key: New encrypted API key
            
        Returns:
            True if rotated successfully
        """
        pass


class IUsageRepository(ABC):
    """Repository interface for usage tracking."""
    
    @abstractmethod
    async def track_usage(self, usage_data: Dict[str, Any]) -> bool:
        """Track usage for a service.
        
        Args:
            usage_data: Dictionary containing:
                - service_name: Service identifier
                - model_string: Model used
                - input_tokens: Number of input tokens
                - output_tokens: Number of output tokens
                - cost: Calculated cost
                - metadata: Optional additional data
                
        Returns:
            True if tracked successfully
        """
        pass
    
    @abstractmethod
    async def get_usage_summary(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage summary for a time period.
        
        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            service_name: Optional filter by service
            
        Returns:
            Summary dictionary with total_cost, total_tokens, by_model, etc.
        """
        pass
    
    @abstractmethod
    async def get_daily_costs(self, days: int = 7) -> Dict[str, Decimal]:
        """Get daily costs for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            Dictionary mapping dates to costs
        """
        pass
    
    @abstractmethod
    async def get_service_usage(
        self,
        service_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get detailed usage for a specific service.
        
        Args:
            service_name: Service identifier
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Detailed usage statistics for the service
        """
        pass
    
    @abstractmethod
    async def estimate_monthly_cost(self, based_on_days: int = 7) -> Decimal:
        """Estimate monthly cost based on recent usage.
        
        Args:
            based_on_days: Number of recent days to base estimate on
            
        Returns:
            Estimated monthly cost
        """
        pass