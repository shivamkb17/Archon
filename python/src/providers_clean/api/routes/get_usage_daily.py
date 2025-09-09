from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_usage_service
from ...services import UsageService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/usage/daily")
async def get_daily_costs(
    days: int = 7,
    tracker: UsageService = Depends(get_usage_service)
):
    """Get daily costs for the last N days"""
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400, detail="days must be between 1 and 365")
    try:
        daily_costs = await tracker.get_daily_costs(days)
        return daily_costs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily costs: {str(e)}"
        )
