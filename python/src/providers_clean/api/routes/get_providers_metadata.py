import logging
from typing import Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service
from ..schemas import ProviderMetadata
from ...models.openrouter_models import OpenRouterService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/providers/metadata", response_model=Dict[str, ProviderMetadata])
async def get_providers_metadata(
    sync_service: ModelSyncService = Depends(get_model_sync_service)
)-> Dict[str, ProviderMetadata]:
    """Get metadata for all providers"""
    try:
        async with sync_service.uow as uow:
            repo = uow.available_models
            if repo is None:
                raise HTTPException(status_code=500, detail="Available models repository not initialized")
            stats = await repo.get_provider_statistics()

            metadata: Dict[str, ProviderMetadata] = {}
            for provider, provider_stats in stats.items():
                # Safely parse last_sync to datetime if possible
                last_sync_val = provider_stats.get('last_sync')
                last_sync: datetime | None = None
                if isinstance(last_sync_val, str):
                    try:
                        last_sync = datetime.fromisoformat(last_sync_val)
                    except Exception:
                        last_sync = None
                elif isinstance(last_sync_val, datetime):
                    last_sync = last_sync_val

                metadata[provider] = ProviderMetadata(
                    provider=provider,
                    model_count=int(provider_stats.get('active_models', 0) or 0),
                    max_context_length=int(provider_stats.get('max_context_length', 0) or 0),
                    min_input_cost=(float(provider_stats['min_cost']) if provider_stats.get('min_cost') else None),
                    max_input_cost=(float(provider_stats['max_cost']) if provider_stats.get('max_cost') else None),
                    has_free_models=bool(provider_stats.get('free_models', 0) > 0),
                    supports_vision=bool(provider_stats.get('vision_models', 0) > 0),
                    supports_tools=bool(provider_stats.get('tool_models', 0) > 0),
                    last_sync=last_sync,
                )

            # If no database metadata, try to generate from OpenRouter
            if not metadata:
                logger.info("No database metadata found, generating from OpenRouter")
                try:
                    all_providers_dict = OpenRouterService.get_all_providers()
                    for provider_name, models in all_providers_dict.items():
                        if models:  # Only include providers with models
                            model_count = len(models)
                            max_context = max((m.context_length or 0) for m in models) if models else 0
                            costs = [m.input_cost for m in models if m.input_cost and m.input_cost > 0]
                            min_cost = min(costs) / 1_000_000 if costs else None  # Convert to per-token
                            max_cost = max(costs) / 1_000_000 if costs else None
                            has_free = any(m.is_free for m in models)
                            supports_vision = any(m.supports_vision for m in models)
                            supports_tools = any(m.supports_tools for m in models)
                            
                            metadata[provider_name] = ProviderMetadata(
                                provider=provider_name,
                                model_count=model_count,
                                max_context_length=max_context,
                                min_input_cost=min_cost,
                                max_input_cost=max_cost,
                                has_free_models=has_free,
                                supports_vision=supports_vision,
                                supports_tools=supports_tools,
                                last_sync=None,
                            )
                    
                    # Add ollama as a local provider
                    metadata['ollama'] = ProviderMetadata(
                        provider='ollama',
                        model_count=4,  # Based on local models we sync
                        max_context_length=8192,
                        min_input_cost=None,
                        max_input_cost=None,
                        has_free_models=True,
                        supports_vision=False,
                        supports_tools=True,
                        last_sync=None,
                    )
                    
                    if metadata:
                        logger.info(f"Generated metadata for {len(metadata)} providers from OpenRouter")
                        return metadata
                except Exception as openrouter_error:
                    logger.error(f"Failed to generate metadata from OpenRouter: {openrouter_error}")
            
            if not metadata:
                raise HTTPException(status_code=404, detail="No provider metadata found in database or OpenRouter")
            return metadata

    except Exception as e:
        logger.error(f"Failed to get providers metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers metadata: {str(e)}")
