from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/{service_name}")
async def get_service_info(
    service_name: str,
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Get detailed information about a specific service"""
    try:
        service = await registry_service.get_service(service_name)
        if service:
            return service
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Service not found: {service_name}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service info: {str(e)}"
        )
