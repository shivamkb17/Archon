from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService, ServiceInfo
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/registry", response_model=List[ServiceInfo])
async def get_service_registry(
    active_only: bool = True,
    category: Optional[str] = None,
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Get all registered services and agents"""
    try:
        services = await registry_service.get_all_services(active_only=active_only, category=category)
        return services
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service registry: {str(e)}"
        )
