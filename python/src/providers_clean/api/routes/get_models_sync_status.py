from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/models/sync/status")
async def get_models_sync_status(
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Get the current model sync status and statistics"""
    try:
        status = await sync_service.get_sync_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )
