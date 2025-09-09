from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/services/{service_name}/deprecate")
async def deprecate_service(
    service_name: str,
    reason: str,
    replacement_service: Optional[str] = None,
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Mark a service as deprecated"""
    try:
        result = await registry_service.deprecate_service(service_name, reason, replacement_service)
        if result:
            return {"status": "success", "service": service_name, "reason": reason}
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
            detail=f"Failed to deprecate service: {str(e)}"
        )
