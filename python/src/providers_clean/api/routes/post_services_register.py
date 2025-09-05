from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService, ServiceRegistration
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/services/register")
async def register_service(
    registration: ServiceRegistration,
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Register a new service or update existing one"""
    try:
        service_info = await registry_service.register_service(registration)
        return service_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register service: {str(e)}"
        )
