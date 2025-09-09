from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_model_service, get_key_service
from ..schemas import ServiceStatus
from ...services import ModelConfigService, APIKeyService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/status", response_model=List[ServiceStatus])
async def get_services_status(
    model_service: ModelConfigService = Depends(get_model_service),
    key_service: APIKeyService = Depends(get_key_service)
):
    """Get status of all configured services"""
    try:
        configs = await model_service.get_all_configs()
        active_providers = await key_service.get_active_providers()
        # Normalize active_providers to lowercase for case-insensitive comparison
        active_providers = {provider.lower() for provider in active_providers}

        status_list: List[ServiceStatus] = []
        for service_name, model_string in configs.items():
            provider = model_string.split(':', 1)[0].lower(
            ) if ':' in model_string else 'unknown'
            model = model_string.split(
                ':', 1)[1] if ':' in model_string else model_string

            full_config = await model_service.get_model_config(service_name)

            # Safe access to full_config fields with defaults
            temperature = getattr(full_config, 'temperature',
                                  0.7) if full_config else 0.7
            max_tokens = getattr(full_config, 'max_tokens',
                                 None) if full_config else None

            status_list.append(ServiceStatus(
                service_name=service_name,
                model_string=model_string,
                provider=provider,
                model=model,
                api_key_configured=provider in active_providers or provider == 'ollama',
                temperature=temperature,
                max_tokens=max_tokens
            ))

        return status_list

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )
