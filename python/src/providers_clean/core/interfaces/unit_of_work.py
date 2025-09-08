"""Unit of Work pattern interface for coordinating repository operations.

The Unit of Work pattern ensures that multiple repository operations
are executed as a single transaction, maintaining data consistency.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Optional
from cryptography.fernet import Fernet
from .repositories import IModelConfigRepository, IApiKeyRepository, IUsageRepository, IAvailableModelsRepository, IServiceRegistryRepository

T = TypeVar('T', bound='IUnitOfWork')


class IUnitOfWork(ABC):
    """Unit of Work interface for managing transactions across repositories."""

    model_configs: Optional[IModelConfigRepository]
    api_keys: Optional[IApiKeyRepository]
    usage: Optional[IUsageRepository]
    available_models: Optional[IAvailableModelsRepository]
    service_registry: Optional[IServiceRegistryRepository]
    cipher: Fernet  # Encryption cipher for API keys

    @abstractmethod
    async def __aenter__(self) -> 'IUnitOfWork':
        """Enter the unit of work context, beginning a transaction."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """Exit the unit of work context, handling transaction completion."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction."""
        pass
