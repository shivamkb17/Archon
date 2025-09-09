from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_usage_service
from ...services import UsageService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/usage/summary")
async def get_usage_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service_name: Optional[str] = None,
    tracker: UsageService = Depends(get_usage_service)
):
    """Get usage summary across all services"""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
        )
    try:
        summary = await tracker.get_usage_summary(start_date, end_date, service_name)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage summary: {str(e)}"
        )
