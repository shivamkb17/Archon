from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_key_service
from ...services import APIKeyService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/api-keys/test/{provider}")
async def test_api_key(
    provider: str,
    service: APIKeyService = Depends(get_key_service)
):
    """Test if a provider's API key is configured"""
    try:
        is_valid = await service.test_provider_key(provider)
        return {
            "provider": provider,
            "configured": is_valid,
            "status": "active" if is_valid else "not_configured"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test API key: {str(e)}"
        )

