from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_model_service
from ...services import ModelConfigService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.delete("/models/config/{service_name}")
async def delete_model_config(
    service_name: str,
    service: ModelConfigService = Depends(get_model_service)
):
    """Delete configuration for a service"""
    try:
        result = await service.delete_config(service_name)
        if result:
            return {"status": "success", "service": service_name}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found for {service_name}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )

