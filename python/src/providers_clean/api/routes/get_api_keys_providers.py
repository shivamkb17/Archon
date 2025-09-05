from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_key_service
from ...services import APIKeyService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/api-keys/providers", response_model=List[str])
async def get_active_providers(
    service: APIKeyService = Depends(get_key_service)
):
    """Get list of providers with active API keys"""
    try:
        providers = await service.get_active_providers()
        return providers
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active providers: {str(e)}"
        )

