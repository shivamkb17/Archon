from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_usage_service
from ...services import UsageService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/usage/track")
async def track_usage(
    service_name: str,
    model_string: str,
    input_tokens: int,
    output_tokens: int,
    metadata: Optional[Dict[str, Any]] = None,
    tracker: UsageService = Depends(get_usage_service)
):
    """Track usage for a service"""
    try:
        result = await tracker.track_usage(
            service_name=service_name,
            model_string=model_string,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata
        )
        if result:
            return {"status": "success", "tracked": True}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to track usage"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track usage: {str(e)}"
        )

