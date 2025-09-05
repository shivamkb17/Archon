"""Supabase implementation of the service registry repository."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import Client
from ....core.interfaces.repositories import IServiceRegistryRepository


class SupabaseServiceRegistryRepository(IServiceRegistryRepository):
    """Concrete implementation of service registry repository using Supabase."""
    
    def __init__(self, db_client: Client):
        """Initialize repository with Supabase client.
        
        Args:
            db_client: Supabase client instance
        """
        self.db = db_client
        self.table_name = "service_registry"
    
    async def get_all_services(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all services from the registry.
        
        Args:
            active_only: If True, only return active services
            
        Returns:
            List of service dictionaries
        """
        try:
            query = self.db.table(self.table_name).select('*')
            
            if active_only:
                query = query.eq('is_active', True).eq('is_deprecated', False)
            
            response = query.order('category').order('service_type').order('display_name').execute()
            return response.data or []
            
        except Exception as e:
            print(f"Error getting all services: {e}")
            return []
    
    async def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific service by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service dictionary or None if not found
        """
        try:
            response = self.db.table(self.table_name).select('*').eq(
                'service_name', service_name
            ).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting service {service_name}: {e}")
            return None
    
    async def register_service(self, service_data: Dict[str, Any]) -> str:
        """Register or update a service in the registry.
        
        Args:
            service_data: Dictionary containing service information
            
        Returns:
            Service ID (UUID) of the registered service
        """
        try:
            # Use the register_service database function
            response = self.db.rpc('register_service', {
                'p_service_name': service_data.get('service_name'),
                'p_display_name': service_data.get('display_name'),
                'p_description': service_data.get('description'),
                'p_icon': service_data.get('icon'),
                'p_category': service_data.get('category', 'service'),
                'p_service_type': service_data.get('service_type', 'backend_service'),
                'p_model_type': service_data.get('model_type', 'llm'),
                'p_location': service_data.get('location', 'main_server'),
                'p_supports_temperature': service_data.get('supports_temperature', True),
                'p_supports_max_tokens': service_data.get('supports_max_tokens', True),
                'p_default_model': service_data.get('default_model'),
                'p_cost_profile': service_data.get('cost_profile', 'medium'),
                'p_owner_team': service_data.get('owner_team')
            }).execute()
            
            if response.data:
                return str(response.data)
            else:
                raise Exception("No ID returned from register_service function")
                
        except Exception as e:
            print(f"Error registering service {service_data.get('service_name', 'unknown')}: {e}")
            raise e
    
    async def update_service_metadata(self, service_name: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a service.
        
        Args:
            service_name: Name of the service
            metadata: Dictionary with metadata to update
            
        Returns:
            True if updated successfully
        """
        try:
            # Add updated_at timestamp
            update_data = {**metadata, 'updated_at': datetime.now().isoformat()}
            
            response = self.db.table(self.table_name).update(
                update_data
            ).eq('service_name', service_name).execute()
            
            return len(response.data) > 0 if response.data else False
            
        except Exception as e:
            print(f"Error updating service metadata for {service_name}: {e}")
            return False
    
    async def deprecate_service(self, service_name: str, reason: str, replacement: Optional[str] = None) -> bool:
        """Mark a service as deprecated.
        
        Args:
            service_name: Name of service to deprecate
            reason: Reason for deprecation
            replacement: Optional replacement service
            
        Returns:
            True if deprecated successfully
        """
        try:
            # Use the deprecate_service database function
            response = self.db.rpc('deprecate_service', {
                'p_service_name': service_name,
                'p_reason': reason,
                'p_replacement': replacement
            }).execute()
            
            return bool(response.data)
            
        except Exception as e:
            print(f"Error deprecating service {service_name}: {e}")
            return False
    
    async def get_services_by_category(self, category: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get services filtered by category.
        
        Args:
            category: Category ('agent' or 'service')
            active_only: If True, only return active services
            
        Returns:
            List of service dictionaries
        """
        try:
            query = self.db.table(self.table_name).select('*').eq('category', category)
            
            if active_only:
                query = query.eq('is_active', True).eq('is_deprecated', False)
            
            response = query.order('service_type').order('display_name').execute()
            return response.data or []
            
        except Exception as e:
            print(f"Error getting services by category {category}: {e}")
            return []
    
    async def get_unregistered_services(self) -> List[Dict[str, Any]]:
        """Get services that have configurations but no registry entries.
        
        Returns:
            List of unregistered service information
        """
        try:
            # Use the unregistered_services view
            response = self.db.from_('unregistered_services').select('*').execute()
            return response.data or []
            
        except Exception as e:
            print(f"Error getting unregistered services: {e}")
            return []