import asyncio
from fastapi import APIRouter, Depends, HTTPException

from ...services import ServiceRegistryService, ModelSyncService
from ...infrastructure.dependencies import get_service_registry_service, get_model_sync_service


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/services/agents")
async def get_agents_registry(
    active_only: bool = True,
    registry_service: ServiceRegistryService = Depends(
        get_service_registry_service),
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Get all registered PydanticAI agents"""
    try:
        # Opportunistic bootstrap if data is stale or missing; non-blocking
        try:
            if await sync_service.should_sync(max_age_hours=24):
                asyncio.create_task(
                    sync_service.full_sync(force_refresh=False))
                asyncio.create_task(
                    registry_service.sync_registry_with_model_configs())
        except Exception:
            pass
        agents = await registry_service.get_agents(active_only=active_only)
        if not agents:
            raise HTTPException(
                status_code=404, detail="No agents found in database")
        return agents
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agents registry: {str(e)}"
        )
