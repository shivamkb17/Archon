from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/registry/statistics")
async def get_registry_statistics(
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Get comprehensive statistics about the service registry"""
    try:
        stats = await registry_service.get_registry_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get registry statistics: {str(e)}"
        )
