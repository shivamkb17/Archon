import logging
from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/services/registry/initialize")
async def initialize_service_registry(
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Initialize/repair the service registry by discovering services from DB.

    This discovers unregistered services from model_config (via DB view or logic)
    and registers them. No hardcoded frontend configs are used.
    """
    try:
        sync_result = await registry_service.sync_registry_with_model_configs()
        return {
            "status": sync_result.get('status', 'success'),
            "services_discovered": sync_result.get('services_discovered', 0),
            "services_registered": sync_result.get('services_registered', 0),
            "message": "Service registry synchronized with database model configs"
        }
    except Exception as e:
        logger.error(f"Failed to initialize service registry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize service registry: {str(e)}"
        )
