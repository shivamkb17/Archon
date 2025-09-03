"""Supabase implementation of the Unit of Work pattern."""

from typing import Any, Optional
from supabase import Client
from cryptography.fernet import Fernet
from ...core.interfaces.unit_of_work import IUnitOfWork
from ..repositories.supabase import (
    SupabaseModelConfigRepository,
    SupabaseApiKeyRepository,
    SupabaseUsageRepository
)


class SupabaseUnitOfWork(IUnitOfWork):
    """Concrete Unit of Work implementation for Supabase.
    
    Note: Supabase doesn't support traditional transactions via the Python client,
    so this implementation provides a logical grouping of operations with
    best-effort consistency.
    """
    
    def __init__(self, db_client: Client, cipher: Optional[Fernet] = None):
        """Initialize Unit of Work with Supabase client.
        
        Args:
            db_client: Supabase client instance
            cipher: Optional Fernet cipher for API key encryption
        """
        self.db = db_client
        self.cipher = cipher or Fernet(Fernet.generate_key())
        self._in_transaction = False
        
        # Initialize repositories (will be set in __aenter__)
        self.model_configs = None
        self.api_keys = None
        self.usage = None
    
    async def __aenter__(self):
        """Enter the unit of work context.
        
        Initializes repositories and marks the start of a logical transaction.
        """
        self._in_transaction = True
        
        # Initialize repositories
        self.model_configs = SupabaseModelConfigRepository(self.db)
        self.api_keys = SupabaseApiKeyRepository(self.db, self.cipher)
        self.usage = SupabaseUsageRepository(self.db)
        
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """Exit the unit of work context.
        
        Handles any cleanup and marks the end of the logical transaction.
        """
        self._in_transaction = False
        
        # If there was an exception, we would rollback here
        # Since Supabase doesn't have client-side transactions,
        # we rely on individual operation atomicity
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        
        # Clear repository references
        self.model_configs = None
        self.api_keys = None
        self.usage = None
    
    async def commit(self):
        """Commit the current transaction.
        
        Note: Since Supabase operations are auto-committed,
        this is primarily for compatibility with the interface.
        """
        # In a real transaction system, we would commit here
        # For Supabase, operations are already committed
        pass
    
    async def rollback(self):
        """Rollback the current transaction.
        
        Note: Since Supabase doesn't support client-side transactions,
        this method exists for interface compatibility but doesn't
        perform actual rollback operations.
        """
        # In a real transaction system, we would rollback here
        # For Supabase, we can't rollback already committed operations
        # This could be enhanced with compensation logic if needed
        pass