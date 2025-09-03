"""Refactored provider routes using the new repository-based architecture."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, SecretStr

# Import new services and dependencies
from ..infrastructure.dependencies import get_unit_of_work, get_model_sync_service
from ..core.interfaces.unit_of_work import IUnitOfWork
from ..services import (
    ModelConfigService,
    APIKeyService,
    UsageService,
    ModelConfig,
    ModelSyncService
)

# Models and services are now managed through database - legacy imports removed

router = APIRouter(prefix="/api/providers", tags=["providers"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class ModelSelectionRequest(BaseModel):
    """Request to update model selection"""
    service_name: str = Field(..., description="Service name (e.g., 'rag_agent')")
    model_string: str = Field(..., description="Model string (e.g., 'openai:gpt-4o')")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)


class APIKeyRequest(BaseModel):
    """Request to set an API key"""
    provider: str = Field(..., description="Provider name (e.g., 'openai')")
    api_key: SecretStr = Field(..., description="API key to store")
    base_url: Optional[str] = Field(None, description="Optional base URL")


class AvailableModel(BaseModel):
    """Available model information"""
    provider: str
    model: str
    model_string: str
    display_name: str
    has_api_key: bool
    cost_tier: Optional[str] = None
    estimated_cost_per_1k: Optional[Dict[str, float]] = None
    is_embedding: bool = False
    model_id: Optional[str] = None
    description: Optional[str] = None
    context_length: Optional[int] = None
    input_cost: Optional[float] = None
    output_cost: Optional[float] = None
    supports_vision: bool = False
    supports_tools: bool = False
    supports_reasoning: bool = False


class ServiceStatus(BaseModel):
    """Service configuration status"""
    service_name: str
    model_string: str
    provider: str
    model: str
    api_key_configured: bool
    temperature: float
    max_tokens: Optional[int]


# ==================== Dependency Injection ====================

def get_model_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> ModelConfigService:
    """Get model configuration service"""
    return ModelConfigService(uow)


def get_key_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> APIKeyService:
    """Get API key service"""
    return APIKeyService(uow)


def get_usage_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> UsageService:
    """Get usage tracking service"""
    return UsageService(uow)


# ==================== Model Configuration Endpoints ====================

@router.get("/models/config/{service_name}", response_model=ModelConfig)
async def get_model_config(
    service_name: str,
    service: ModelConfigService = Depends(get_model_service)
):
    """Get current model configuration for a service"""
    try:
        config = await service.get_model_config(service_name)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model config: {str(e)}"
        )


@router.post("/models/config", response_model=ModelConfig)
async def update_model_config(
    request: ModelSelectionRequest,
    service: ModelConfigService = Depends(get_model_service)
):
    """Update model configuration for a service"""
    try:
        config = await service.set_model_config(
            service_name=request.service_name,
            model_string=request.model_string,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model config: {str(e)}"
        )


@router.get("/models/configs", response_model=Dict[str, str])
async def get_all_model_configs(
    service: ModelConfigService = Depends(get_model_service)
):
    """Get all service model configurations"""
    try:
        configs = await service.get_all_configs()
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configurations: {str(e)}"
        )


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


# ==================== API Key Management Endpoints ====================

@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def set_api_key(
    request: APIKeyRequest,
    service: APIKeyService = Depends(get_key_service)
):
    """Store an API key for a provider"""
    try:
        result = await service.set_api_key(
            provider=request.provider,
            api_key=request.api_key.get_secret_value(),
            base_url=request.base_url
        )
        if result:
            return {"status": "success", "provider": request.provider}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store API key"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store API key: {str(e)}"
        )


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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active providers: {str(e)}"
        )


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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active API key found for {provider}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate API key: {str(e)}"
        )


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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test API key: {str(e)}"
        )


# ==================== Usage Tracking Endpoints ====================

@router.get("/usage/summary")
async def get_usage_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service_name: Optional[str] = None,
    tracker: UsageService = Depends(get_usage_service)
):
    """Get usage summary across all services"""
    try:
        summary = await tracker.get_usage_summary(start_date, end_date, service_name)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage summary: {str(e)}"
        )


@router.get("/usage/daily")
async def get_daily_costs(
    days: int = 7,
    tracker: UsageService = Depends(get_usage_service)
):
    """Get daily costs for the last N days"""
    try:
        daily_costs = await tracker.get_daily_costs(days)
        return daily_costs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily costs: {str(e)}"
        )


@router.get("/usage/estimate-monthly")
async def estimate_monthly_cost(
    tracker: UsageService = Depends(get_usage_service)
):
    """Estimate monthly cost based on current usage"""
    try:
        estimate = await tracker.estimate_monthly_cost()
        return {
            "estimated_monthly_cost": estimate,
            "based_on_days": 7
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate monthly cost: {str(e)}"
        )


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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track usage"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track usage: {str(e)}"
        )


# ==================== Available Models Endpoint ====================

@router.get("/models/available", response_model=List[AvailableModel])
async def get_available_models(
    key_service: APIKeyService = Depends(get_key_service),
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Get list of available models from database, filtered by configured API keys"""
    try:
        # Get active providers with API keys
        active_providers = await key_service.get_active_providers()
        
        # Always include ollama as it doesn't need API keys
        all_providers = list(set(active_providers + ['ollama']))
        
        # Note: Removed automatic sync on API call to prevent database spam
        # Use the dedicated /models/sync endpoint or background scheduler for syncing
        
        # Get models from database for providers with API keys
        async with sync_service.uow as uow:
            db_models = await uow.available_models.get_providers_with_api_keys(all_providers)
        
        # Convert database format to API response format
        available_models = []
        for db_model in db_models:
            # Determine has_api_key status
            has_api_key = db_model['provider'] in active_providers or db_model['provider'] == 'ollama'
            
            # Calculate estimated cost per 1k tokens for display
            estimated_cost_per_1k = None
            if db_model['input_cost'] and db_model['input_cost'] > 0:
                estimated_cost_per_1k = {
                    'input': float(db_model['input_cost']) * 1000,  # Convert per-token to per-1k
                    'output': float(db_model['output_cost'] or 0) * 1000
                }
            
            available_models.append(AvailableModel(
                provider=db_model['provider'],
                model=db_model['model_id'],
                model_string=db_model['model_string'],
                display_name=db_model['display_name'],
                has_api_key=has_api_key,
                cost_tier=db_model['cost_tier'],
                estimated_cost_per_1k=estimated_cost_per_1k,
                is_embedding=db_model['is_embedding'],
                model_id=db_model['model_id'],
                description=db_model['description'],
                context_length=db_model['context_length'],
                input_cost=float(db_model['input_cost']) * 1_000_000 if db_model['input_cost'] else 0,  # Convert to per-1M for compatibility
                output_cost=float(db_model['output_cost']) * 1_000_000 if db_model['output_cost'] else 0,
                supports_vision=db_model['supports_vision'],
                supports_tools=db_model['supports_tools'],
                supports_reasoning=db_model['supports_reasoning']
            ))
        
        logger.info(f"Returned {len(available_models)} models from database for {len(all_providers)} providers")
        return available_models
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available models: {str(e)}"
        )


# ==================== Service Status Endpoint ====================

@router.get("/status", response_model=List[ServiceStatus])
async def get_services_status(
    model_service: ModelConfigService = Depends(get_model_service),
    key_service: APIKeyService = Depends(get_key_service)
):
    """Get status of all configured services"""
    try:
        configs = await model_service.get_all_configs()
        active_providers = await key_service.get_active_providers()
        
        status_list = []
        for service_name, model_string in configs.items():
            provider = model_string.split(':', 1)[0] if ':' in model_string else 'unknown'
            model = model_string.split(':', 1)[1] if ':' in model_string else model_string
            
            # Get full config for temperature and max_tokens
            full_config = await model_service.get_model_config(service_name)
            
            status_list.append(ServiceStatus(
                service_name=service_name,
                model_string=model_string,
                provider=provider,
                model=model,
                api_key_configured=provider in active_providers or provider == 'ollama',
                temperature=full_config.temperature,
                max_tokens=full_config.max_tokens
            ))
        
        return status_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


# ==================== Initialize System Endpoint ====================

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize provider system: {str(e)}"
        )


# ==================== Model Sync Management Endpoints ====================

@router.post("/models/sync")
async def sync_models_from_sources(
    force_refresh: bool = False,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Manually trigger a sync of all models from external sources"""
    try:
        result = await sync_service.full_sync(force_refresh=force_refresh)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync models: {str(e)}"
        )


@router.get("/models/sync/status")
async def get_models_sync_status(
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Get the current model sync status and statistics"""
    try:
        status = await sync_service.get_sync_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/models/{model_string}/activate")
async def activate_model(
    model_string: str,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Manually activate a model"""
    try:
        # Decode URL-encoded model string (e.g., openai%3Agpt-4o -> openai:gpt-4o)
        import urllib.parse
        decoded_model_string = urllib.parse.unquote(model_string)
        
        result = await sync_service.reactivate_model(decoded_model_string)
        if result:
            return {"status": "success", "model": decoded_model_string}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {decoded_model_string}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model: {str(e)}"
        )


@router.post("/models/{model_string}/deactivate")
async def deactivate_model(
    model_string: str,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Manually deactivate a model"""
    try:
        # Decode URL-encoded model string
        import urllib.parse
        decoded_model_string = urllib.parse.unquote(model_string)
        
        result = await sync_service.deactivate_model(decoded_model_string)
        if result:
            return {"status": "success", "model": decoded_model_string}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {decoded_model_string}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate model: {str(e)}"
        )


@router.post("/models/initialize")
async def initialize_models_database(
    force_refresh: bool = False,
    sync_service: ModelSyncService = Depends(get_model_sync_service)
):
    """Initialize the models database with data from external sources"""
    try:
        logger.info("Initializing models database...")
        
        # Perform initial sync to populate database
        result = await sync_service.full_sync(force_refresh=force_refresh)
        
        # Get final counts
        status = await sync_service.get_sync_status()
        
        return {
            "status": "initialized",
            "sync_result": result,
            "total_models": status.get('active_models', 0),
            "providers": len(status.get('providers', {})),
            "message": "Models database initialized successfully"
        }
    except Exception as e:
        logger.error(f"Failed to initialize models database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize models database: {str(e)}"
        )