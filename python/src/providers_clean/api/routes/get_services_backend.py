from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ..deps import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/backend")
async def get_backend_services_registry(
    active_only: bool = True,
    registry_service: ServiceRegistryService = Depends(
        get_service_registry_service)
):
    """Get all registered backend services"""
    try:
        services = await registry_service.get_backend_services(active_only=active_only)
        return services
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backend services registry: {str(e)}"
        )
