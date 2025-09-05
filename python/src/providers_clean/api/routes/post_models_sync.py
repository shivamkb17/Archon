from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/models/sync")
async def sync_models_from_sources(
    force_refresh: bool = False,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Manually trigger a sync of all models from external sources"""
    try:
        result = await sync_service.full_sync(force_refresh=force_refresh)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync models: {str(e)}"
        )
