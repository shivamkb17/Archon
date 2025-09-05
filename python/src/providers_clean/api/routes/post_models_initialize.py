import logging
from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService
from ...infrastructure.dependencies import get_model_sync_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/models/initialize")
async def initialize_models_database(
    force_refresh: bool = False,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Initialize the models database with data from external sources"""
    try:
        logger.info("Initializing models database...")
        result = await sync_service.full_sync(force_refresh=force_refresh)
        status = await sync_service.get_sync_status()
        return {
            "status": "initialized",
            "sync_result": result,
            "total_models": status.get('active_models', 0),
            "providers": len(status.get('providers', {})),
            "message": "Models database initialized successfully"
        }
    except Exception as e:
        logger.error(f"Failed to initialize models database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize models database: {str(e)}"
        )
