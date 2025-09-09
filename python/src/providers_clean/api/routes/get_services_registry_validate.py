from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService
from ...infrastructure.dependencies import get_service_registry_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/registry/validate")
async def validate_registry_completeness(
    registry_service: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Validate that service registry is complete and consistent"""
    try:
        validation_result = await registry_service.validate_registry_completeness()
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate registry: {str(e)}"
        )
