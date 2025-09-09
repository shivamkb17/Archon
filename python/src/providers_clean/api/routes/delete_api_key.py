from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_key_service
from ...services import APIKeyService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.delete("/api-keys/{provider}")
async def deactivate_api_key(
    provider: str,
    service: APIKeyService = Depends(get_key_service)
):
    """Deactivate an API key for a provider"""
    try:
        success = await service.deactivate_api_key(provider)
        if success:
            return {"status": "success", "provider": provider}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No active API key found for {provider}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate API key: {str(e)}"
        )

