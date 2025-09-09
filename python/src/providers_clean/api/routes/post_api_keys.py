import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_key_service
from ..schemas import APIKeyRequest
from ...services import APIKeyService, ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])






@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def set_api_key(
    request: APIKeyRequest,
    service: APIKeyService = Depends(get_key_service),
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Store an API key for a provider"""
    try:
        result = await service.set_api_key(
            provider=request.provider,
            api_key=request.api_key.get_secret_value(),
            base_url=request.base_url
        )
        if result:
            # Synchronously sync all models from OpenRouter to ensure they're available immediately  
            try:
                sync_result = await sync_service.full_sync(force_refresh=True)
                logger.info(f"Completed full sync after API key added: {sync_result.get('total_models_synced', 0)} models synced")
            except Exception as sync_error:
                logger.error(f"Model sync failed after API key added: {sync_error}")
                # Don't fail the API key operation if sync fails
            
            return {"status": "success", "provider": request.provider}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store API key"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store API key: {str(e)}"
        )
