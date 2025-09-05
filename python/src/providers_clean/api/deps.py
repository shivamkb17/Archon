"""Shared FastAPI dependencies for provider routes."""

from fastapi import Depends

from ..core.interfaces.unit_of_work import IUnitOfWork
from ..services import (
    ModelConfigService,
    APIKeyService,
    UsageService,
)
from ..infrastructure.dependencies import get_unit_of_work


def get_model_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> ModelConfigService:
    """Get model configuration service"""
    return ModelConfigService(uow)


def get_key_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> APIKeyService:
    """Get API key service"""
    return APIKeyService(uow)


def get_usage_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> UsageService:
    """Get usage tracking service"""
    return UsageService(uow)

