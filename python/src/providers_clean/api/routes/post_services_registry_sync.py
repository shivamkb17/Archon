from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/services/registry/sync")
async def sync_registry_with_configs(
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Sync service registry with current model configurations"""
    try:
        result = await registry_service.sync_registry_with_model_configs()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync registry: {str(e)}"
        )
