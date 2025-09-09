import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service
from ...models.openrouter_models import OpenRouterService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/providers/list", response_model=List[str])
async def get_providers_list(
    sync_service: ModelSyncService = Depends(get_model_sync_service)
) -> List[str]:
    """Get list of all available provider names from OpenRouter and local providers"""
    try:
        # Get all providers from OpenRouter (this fetches from API)
        all_providers_dict = await OpenRouterService.get_all_providers_async()
        openrouter_providers = list(all_providers_dict.keys())

        # Add local providers that are always available
        local_providers = ['ollama']

        # Combine and sort providers
        all_providers = sorted(set(openrouter_providers + local_providers))

        if not all_providers:
            raise HTTPException(
                status_code=404, detail="No providers available from OpenRouter API")

        logger.info(
            f"Retrieved {len(all_providers)} providers from OpenRouter and local sources")
        return all_providers

    except Exception as e:
        logger.error(f"Failed to get providers list from OpenRouter: {e}")
        # Fallback to database providers if OpenRouter fails
        try:
            async with sync_service.uow as uow:
                repo = uow.available_models
                if repo is None:
                    raise HTTPException(
                        status_code=500, detail="Available models repository not initialized")
                models = await repo.get_all_models(active_only=True)
                providers = sorted(set(model['provider'] for model in models))
                if providers:
                    logger.info(
                        f"Fallback: Retrieved {len(providers)} providers from database")
                    return providers
                else:
                    raise HTTPException(
                        status_code=404, detail="No providers found in database or OpenRouter")
        except Exception as db_error:
            logger.error(f"Database fallback also failed: {db_error}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get providers from both OpenRouter and database: {str(e)}")
