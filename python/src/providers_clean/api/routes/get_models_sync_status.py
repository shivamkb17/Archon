from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import logging
import traceback
from typing import Dict, Any, Optional

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


logger = logging.getLogger(__name__)


class SyncStatusResponse(BaseModel):
    total_models: int
    active_models: int
    inactive_models: int
    providers: Dict[str, Any]
    last_check: str
    error: Optional[str] = None


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/models/sync/status", response_model=SyncStatusResponse)
async def get_models_sync_status(
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Get the current model sync status and statistics"""
    try:
        status = await sync_service.get_sync_status()
        return status
    except Exception:
        logger.error(f"Error getting sync status: {traceback.format_exc()}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
