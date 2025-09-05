from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_usage_service
from ...services import UsageService
from ..schemas import MonthlyCostEstimate


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/usage/estimate-monthly", response_model=MonthlyCostEstimate)
async def estimate_monthly_cost(
    tracker: UsageService = Depends(get_usage_service)
) -> MonthlyCostEstimate:
    """Estimate monthly cost based on current usage"""
    try:
        estimate = await tracker.estimate_monthly_cost()
        return MonthlyCostEstimate(estimated_monthly_cost=estimate, based_on_days=7)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to estimate monthly cost: {str(e)}"
        )
