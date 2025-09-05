"""Service for syncing available models from external sources to database."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.interfaces.unit_of_work import IUnitOfWork
from ..models.openrouter_models import OpenRouterService, ProviderModel


logger = logging.getLogger(__name__)


class ModelSyncService:
    """Service for syncing available AI models from external sources to database."""
    
    def __init__(self, uow: IUnitOfWork):
        """Initialize service with Unit of Work.
        
        Args:
            uow: Unit of Work instance for repository access
        """
        self.uow = uow
    
    async def sync_from_openrouter(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Sync models from OpenRouter API to database.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary with sync results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting OpenRouter model sync...")
        
        try:
            # Fetch models from OpenRouter (uses cache unless force_refresh)
            if force_refresh:
                # Clear cache by forcing a fresh fetch
                OpenRouterService.get_all_providers.cache_clear()
            
            all_providers = OpenRouterService.get_all_providers()
            
            # Convert to our database format
            models_to_sync = []
            
            for provider_name, provider_models in all_providers.items():
                logger.info(f"Processing {provider_name}: {len(provider_models)} models")
                for model in provider_models:
                    try:
                        model_data = self._convert_provider_model_to_dict(model)
                        models_to_sync.append(model_data)
                    except Exception as conv_error:
                        logger.error(f"Failed to convert model {model.model_id}: {conv_error}")
            
            logger.info(f"Converted {len(models_to_sync)} models for database sync")
            
            # Perform bulk sync using the repository
            async with self.uow as uow:
                try:
                    sync_count = await uow.available_models.bulk_sync_models(
                        models_to_sync, 
                        source='openrouter'
                    )
                    logger.info(f"Database bulk_sync_models returned: {sync_count}")
                except Exception as db_error:
                    logger.error(f"Database sync failed: {db_error}", exc_info=True)
                    # Return error status instead of swallowing the exception
                    return {
                        'status': 'error',
                        'error': f'Database sync failed: {str(db_error)}',
                        'models_synced': 0,
                        'models_deactivated': 0,
                        'sync_duration_seconds': (datetime.now() - start_time).total_seconds(),
                        'sync_time': start_time.isoformat()
                    }
                
                # Deactivate models that weren't in this sync
                deactivated_count = await uow.available_models.deactivate_stale_models(
                    source='openrouter',
                    sync_time=start_time
                )
            
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'models_synced': sync_count,
                'models_deactivated': deactivated_count,
                'total_providers': len(all_providers),
                'sync_duration_seconds': sync_duration,
                'sync_time': start_time.isoformat(),
                'forced_refresh': force_refresh
            }
            
            logger.info(
                f"OpenRouter sync completed: {sync_count} models synced, "
                f"{deactivated_count} deactivated in {sync_duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"OpenRouter sync failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'status': 'error',
                'error': error_msg,
                'models_synced': 0,
                'models_deactivated': 0,
                'sync_duration_seconds': (datetime.now() - start_time).total_seconds(),
                'sync_time': start_time.isoformat()
            }
    
    async def sync_local_models(self) -> Dict[str, Any]:
        """Sync local models (e.g., Ollama) that aren't from OpenRouter.
        
        Returns:
            Dictionary with sync results
        """
        logger.info("Syncing local models...")
        start_time = datetime.now()
        
        # Define common local models
        local_models = [
            {
                'provider': 'ollama',
                'model_id': 'llama3',
                'model_string': 'ollama:llama3',
                'display_name': 'Llama 3 (Local)',
                'description': 'Local Llama 3 model for offline inference',
                'context_length': 8192,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'is_free': True,
                'cost_tier': 'free',
                'is_embedding': False,
                'supports_vision': False,
                'supports_tools': True,
                'supports_reasoning': False,
                'source': 'local'
            },
            {
                'provider': 'ollama',
                'model_id': 'mistral',
                'model_string': 'ollama:mistral',
                'display_name': 'Mistral (Local)',
                'description': 'Local Mistral model for offline inference',
                'context_length': 8192,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'is_free': True,
                'cost_tier': 'free',
                'is_embedding': False,
                'supports_vision': False,
                'supports_tools': True,
                'supports_reasoning': False,
                'source': 'local'
            },
            {
                'provider': 'ollama',
                'model_id': 'codellama',
                'model_string': 'ollama:codellama',
                'display_name': 'Code Llama (Local)',
                'description': 'Local Code Llama model specialized for programming tasks',
                'context_length': 8192,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'is_free': True,
                'cost_tier': 'free',
                'is_embedding': False,
                'supports_vision': False,
                'supports_tools': True,
                'supports_reasoning': False,
                'source': 'local'
            },
            {
                'provider': 'ollama',
                'model_id': 'phi3',
                'model_string': 'ollama:phi3',
                'display_name': 'Phi-3 (Local)',
                'description': 'Local Microsoft Phi-3 model optimized for efficiency',
                'context_length': 8192,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'is_free': True,
                'cost_tier': 'free',
                'is_embedding': False,
                'supports_vision': False,
                'supports_tools': True,
                'supports_reasoning': False,
                'source': 'local'
            }
        ]
        
        try:
            async with self.uow as uow:
                sync_count = await uow.available_models.bulk_sync_models(
                    local_models,
                    source='local'
                )
            
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'models_synced': sync_count,
                'sync_duration_seconds': sync_duration,
                'sync_time': start_time.isoformat()
            }
            
            logger.info(f"Local models sync completed: {sync_count} models synced")
            return result
            
        except Exception as e:
            error_msg = f"Local models sync failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'status': 'error',
                'error': error_msg,
                'models_synced': 0,
                'sync_duration_seconds': (datetime.now() - start_time).total_seconds(),
                'sync_time': start_time.isoformat()
            }
    
    async def full_sync(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Perform a complete sync of all model sources.
        
        Args:
            force_refresh: If True, force fresh fetch from APIs
            
        Returns:
            Combined sync results
        """
        logger.info("Starting full model sync...")
        start_time = datetime.now()
        
        # Run both syncs concurrently
        results = await asyncio.gather(
            self.sync_from_openrouter(force_refresh),
            self.sync_local_models(),
            return_exceptions=True
        )
        
        openrouter_result = results[0] if not isinstance(results[0], Exception) else {'status': 'error', 'error': str(results[0]), 'models_synced': 0}
        local_result = results[1] if not isinstance(results[1], Exception) else {'status': 'error', 'error': str(results[1]), 'models_synced': 0}
        
        total_synced = openrouter_result.get('models_synced', 0) + local_result.get('models_synced', 0)
        total_deactivated = openrouter_result.get('models_deactivated', 0)
        
        sync_duration = (datetime.now() - start_time).total_seconds()
        
        combined_result = {
            'status': 'success' if openrouter_result.get('status') == 'success' and local_result.get('status') == 'success' else 'partial',
            'total_models_synced': total_synced,
            'models_deactivated': total_deactivated,
            'openrouter_result': openrouter_result,
            'local_result': local_result,
            'sync_duration_seconds': sync_duration,
            'sync_time': start_time.isoformat()
        }
        
        if combined_result['status'] == 'success':
            logger.info(f"Full sync completed successfully: {total_synced} models synced, {total_deactivated} deactivated")
        else:
            logger.warning(f"Full sync completed with errors: {total_synced} models synced")
        
        return combined_result
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status and statistics.
        
        Returns:
            Dictionary with sync status and model statistics
        """
        try:
            async with self.uow as uow:
                # Get provider statistics
                stats = await uow.available_models.get_provider_statistics()
                
                # Get total counts
                all_models = await uow.available_models.get_all_models(active_only=False)
                active_models = await uow.available_models.get_all_models(active_only=True)
                
                return {
                    'total_models': len(all_models),
                    'active_models': len(active_models),
                    'inactive_models': len(all_models) - len(active_models),
                    'providers': stats,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def should_sync(self, max_age_hours: int = 24) -> bool:
        """Check if a sync is needed based on the age of the data.
        
        Args:
            max_age_hours: Maximum age in hours before sync is needed
            
        Returns:
            True if sync is recommended
        """
        try:
            stats = await self.get_sync_status()
            providers = stats.get('providers', {})
            
            if not providers:
                return True  # No data, definitely need sync
            
            # Check if any provider data is stale
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for provider_stats in providers.values():
                last_sync = provider_stats.get('last_sync')
                if not last_sync:
                    return True  # No sync time recorded
                
                last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                if last_sync_time < cutoff_time:
                    return True  # Data is stale
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return True  # On error, assume sync is needed
    
    def _convert_provider_model_to_dict(self, model: ProviderModel) -> Dict[str, Any]:
        """Convert ProviderModel to dictionary format for database storage.
        
        Args:
            model: ProviderModel instance
            
        Returns:
            Dictionary suitable for database storage
        """
        # Determine cost tier based on input cost
        if model.is_free:
            cost_tier = 'free'
        elif model.input_cost < 0.5:  # Less than $0.50 per 1M tokens
            cost_tier = 'low'
        elif model.input_cost < 5:    # Less than $5 per 1M tokens
            cost_tier = 'medium'
        else:
            cost_tier = 'high'
        
        return {
            'provider': model.provider,
            'model_id': model.model_id,
            'model_string': f"{model.provider}:{model.model_id}",
            'display_name': model.display_name,
            'description': model.description[:500] if model.description else None,  # Limit description length
            'context_length': model.context_length,
            'input_cost': model.input_cost / 1_000_000 if model.input_cost else 0,  # Convert to per-token cost
            'output_cost': model.output_cost / 1_000_000 if model.output_cost else 0,
            'supports_vision': model.supports_vision,
            'supports_tools': model.supports_tools,
            'supports_reasoning': model.supports_reasoning,
            'is_embedding': model.model_id and 'embedding' in model.model_id.lower(),
            'is_free': model.is_free,
            'cost_tier': cost_tier,
            'source': 'openrouter'
        }
    
    async def get_provider_models_from_db(self, provider: str) -> List[Dict[str, Any]]:
        """Get all models for a provider from the database.
        
        Args:
            provider: Provider name
            
        Returns:
            List of model dictionaries from database
        """
        async with self.uow as uow:
            return await uow.available_models.get_models_by_provider(provider)
    
    async def get_available_models_for_api_keys(self, api_key_providers: List[str]) -> List[Dict[str, Any]]:
        """Get available models for providers that have API keys configured.
        
        Args:
            api_key_providers: List of provider names with API keys
            
        Returns:
            List of available models from providers with API keys
        """
        async with self.uow as uow:
            return await uow.available_models.get_providers_with_api_keys(api_key_providers)
    
    async def manually_add_model(
        self,
        provider: str,
        model_id: str,
        display_name: str,
        **kwargs
    ) -> bool:
        """Manually add a custom model to the database.
        
        Args:
            provider: Provider name
            model_id: Model identifier
            display_name: Human-readable name
            **kwargs: Additional model properties
            
        Returns:
            True if added successfully
        """
        try:
            model_data = {
                'provider': provider,
                'model_id': model_id,
                'model_string': f"{provider}:{model_id}",
                'display_name': display_name,
                'description': kwargs.get('description', f'Custom {provider} model'),
                'context_length': kwargs.get('context_length', 4096),
                'input_cost': kwargs.get('input_cost', 0.0),
                'output_cost': kwargs.get('output_cost', 0.0),
                'supports_vision': kwargs.get('supports_vision', False),
                'supports_tools': kwargs.get('supports_tools', False),
                'supports_reasoning': kwargs.get('supports_reasoning', False),
                'is_embedding': kwargs.get('is_embedding', False),
                'is_free': kwargs.get('is_free', True),
                'cost_tier': kwargs.get('cost_tier', 'free'),
                'source': 'manual'
            }
            
            async with self.uow as uow:
                model_id = await uow.available_models.sync_model(model_data)
                
            logger.info(f"Manually added model: {model_data['model_string']}")
            return True
            
        except Exception as e:
            logger.error(f"Error manually adding model {provider}:{model_id}: {e}")
            return False
    
    async def deactivate_model(self, model_string: str) -> bool:
        """Manually deactivate a model.
        
        Args:
            model_string: Model string (e.g., 'openai:gpt-4o')
            
        Returns:
            True if deactivated successfully
        """
        try:
            async with self.uow as uow:
                result = await uow.available_models.set_model_active(model_string, False)
                
            if result:
                logger.info(f"Deactivated model: {model_string}")
            else:
                logger.warning(f"Model not found for deactivation: {model_string}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error deactivating model {model_string}: {e}")
            return False
    
    async def reactivate_model(self, model_string: str) -> bool:
        """Manually reactivate a model.
        
        Args:
            model_string: Model string (e.g., 'openai:gpt-4o')
            
        Returns:
            True if reactivated successfully
        """
        try:
            async with self.uow as uow:
                result = await uow.available_models.set_model_active(model_string, True)
                
            if result:
                logger.info(f"Reactivated model: {model_string}")
            else:
                logger.warning(f"Model not found for reactivation: {model_string}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error reactivating model {model_string}: {e}")
            return False
    
    async def cleanup_old_models(self, days_old: int = 30) -> int:
        """Clean up very old inactive models.
        
        Args:
            days_old: Remove models inactive for this many days
            
        Returns:
            Number of models removed
        """
        # For now, just return 0 - we'll implement this later if needed
        # The migration focuses on soft deletes (is_active flag)
        logger.info(f"Cleanup operation requested for models older than {days_old} days")
        return 0
