from fastapi import APIRouter, Depends, HTTPException

from ...services import ModelSyncService, ServiceRegistryService
from ...infrastructure.dependencies import get_model_sync_service, get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/bootstrap")
async def bootstrap_providers(
    force_refresh: bool = False,
    sync_service: ModelSyncService = Depends(get_model_sync_service),
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Run a full providers bootstrap: sync models and register services.

    - Performs a full model sync to populate available_models
    - Discovers and registers services from model_config into service_registry
    """
    try:
        sync_result = await sync_service.full_sync(force_refresh=force_refresh)
        registry_result = await registry_service.sync_registry_with_model_configs()
        return {
            "status": "success",
            "model_sync": sync_result,
            "registry_sync": registry_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bootstrap failed: {str(e)}")

