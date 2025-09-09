import urllib.parse
from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/models/{model_string}/activate")
async def activate_model(
    model_string: str,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Manually activate a model"""
    try:
        decoded_model_string = urllib.parse.unquote(model_string)
        result = await sync_service.reactivate_model(decoded_model_string)
        if result:
            return {"status": "success", "model": decoded_model_string}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Model not found: {decoded_model_string}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate model: {str(e)}"
        )
