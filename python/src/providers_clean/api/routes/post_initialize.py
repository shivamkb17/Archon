from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_key_service
from ...services import APIKeyService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/initialize")
async def initialize_provider_system(
    key_service: APIKeyService = Depends(get_key_service)
):
    """Initialize the provider system (set up environment variables)"""
    try:
        status = await key_service.setup_environment()
        return {
            "status": "initialized",
            "providers_configured": list(status.keys()),
            "success_count": sum(1 for v in status.values() if v)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize provider system: {str(e)}"
        )

