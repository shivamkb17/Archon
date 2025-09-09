import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_model_service
from ...services import ModelConfigService, ModelConfig


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/models/config/{service_name}", response_model=ModelConfig)
async def get_model_config(
    service_name: str,
    service: ModelConfigService = Depends(get_model_service)
):
    """Get current model configuration for a service"""
    try:
        config = await service.get_model_config(service_name)
        return config
    except ValueError as e:
        # Config not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model config: {str(e)}"
        )
