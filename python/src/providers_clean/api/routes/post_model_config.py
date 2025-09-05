from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_model_service
from ..schemas import ModelSelectionRequest
from ...services import ModelConfigService, ModelConfig, ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/models/config", response_model=ModelConfig)
async def update_model_config(
    request: ModelSelectionRequest,
    service: ModelConfigService = Depends(get_model_service),
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Update model configuration for a service"""
    try:
        config = await service.set_model_config(
            service_name=request.service_name,
            model_string=request.model_string,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        # Best-effort: update registry's default_model so UI reflects latest on refresh
        try:
            await registry_service.update_default_model(
                request.service_name, request.model_string
            )
        except Exception:
            # Don't block success on registry update
            pass

        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model config: {str(e)}"
        )
