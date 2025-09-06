"""Supabase implementation of the model configuration repository."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
from ....core.interfaces.repositories import IModelConfigRepository


class SupabaseModelConfigRepository(IModelConfigRepository):
    """Concrete implementation of model configuration repository using Supabase."""
    
    def __init__(self, db_client: Client):
        """Initialize repository with Supabase client.
        
        Args:
            db_client: Supabase client instance
        """
        self.db = db_client
        self.table_name = "model_config"
    
    async def get_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Configuration dict or None if not found
        """
        try:
            response = self.db.table(self.table_name).select("*").eq(
                "service_name", service_name
            ).execute()
            
            # Check if we got any data
            if response.data and len(response.data) > 0:
                data: Dict[str, Any] = response.data[0]  # Get first result
                return {
                    "service_name": data["service_name"],
                    "model_string": data["model_string"],
                    "temperature": data.get("temperature", 0.7),
                    "max_tokens": data.get("max_tokens"),
                    "embedding_dimensions": data.get("embedding_dimensions"),
                    "batch_size": data.get("batch_size"),
                    "updated_at": data.get("updated_at"),
                    "updated_by": data.get("updated_by")
                }
            return None
            
        except Exception as e:
            # Log error but return None for not found
            print(f"Error getting config for {service_name}: {e}")
            return None
    
    async def save_config(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update model configuration for a service.
        
        Args:
            service_name: Name of the service
            config: Configuration dictionary
            
        Returns:
            Saved configuration dictionary
        """
        data = {
            "service_name": service_name,
            "model_string": config["model_string"],
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens"),
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": config.get("updated_by", "system")
        }
        
        # Try to update first
        existing = await self.get_config(service_name)
        
        if existing:
            # Update existing configuration
            response = self.db.table(self.table_name).update(data).eq(
                "service_name", service_name
            ).execute()
        else:
            # Insert new configuration
            response = self.db.table(self.table_name).insert(data).execute()
        
        if response.data and len(response.data) > 0:
            result: Dict[str, Any] = response.data[0]
            return {
                "service_name": result["service_name"],
                "model_string": result["model_string"],
                "temperature": result.get("temperature", 0.7),
                "max_tokens": result.get("max_tokens")
            }
        
        raise Exception(f"Failed to save configuration for {service_name}")
    
    async def get_all_configs(self) -> Dict[str, str]:
        """Get all service configurations.
        
        Returns:
            Dictionary mapping service names to model strings
        """
        response = self.db.table(self.table_name).select(
            "service_name", "model_string"
        ).execute()
        
        if response.data:
            return {
                config["service_name"]: config["model_string"]
                for config in response.data
                if isinstance(config, dict)
            }
        return {}
    
    async def delete_config(self, service_name: str) -> bool:
        """Delete configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deleted, False if not found
        """
        try:
            response = self.db.table(self.table_name).delete().eq(
                "service_name", service_name
            ).execute()
            
            # Check if any rows were deleted
            return len(response.data) > 0 if response.data else False
            
        except Exception:
            return False
    
    async def bulk_update_provider(self, old_provider: str, new_provider: str, new_models: Dict[str, str]) -> int:
        """Update all configurations using a specific provider.
        
        Args:
            old_provider: Current provider name
            new_provider: New provider name
            new_models: Mapping of old model strings to new ones
            
        Returns:
            Number of configurations updated
        """
        # Get all configurations using the old provider
        response = self.db.table(self.table_name).select("*").execute()
        
        if not response.data:
            return 0
        
        updated_count = 0
        for config in response.data:
            config: Dict[str, Any] = config
            model_string = config["model_string"]
            
            # Check if this configuration uses the old provider
            if model_string.startswith(f"{old_provider}:"):
                # Update to new model string
                new_model_string = new_models.get(
                    model_string,
                    model_string.replace(f"{old_provider}:", f"{new_provider}:")
                )
                
                # Update the configuration
                update_response = self.db.table(self.table_name).update({
                    "model_string": new_model_string,
                    "updated_at": datetime.utcnow().isoformat(),
                    "updated_by": "bulk_update"
                }).eq("service_name", config["service_name"]).execute()
                
                if update_response.data:
                    updated_count += 1
        
        return updated_count