"""
Settings API - Replaced with Provider Clean System

This module now redirects to the provider_clean system for all configuration management.
The old credential-based settings have been replaced with the modern provider system.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/credentials", deprecated=True)
async def list_credentials():
    """DEPRECATED: Use /api/providers/services/backend and /api/providers/api-keys/providers instead."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED",
            "message": "Credential system has been replaced with provider_clean system",
            "alternatives": [
                "GET /api/providers/services/backend - List all services",
                "GET /api/providers/api-keys/providers - List active providers"
            ]
        }
    )


@router.get("/credentials/{category}", deprecated=True)
async def get_credentials_by_category(category: str):
    """DEPRECATED: Use provider_clean API endpoints instead."""
    if category == "rag_strategy":
        return JSONResponse(
            status_code=410,
            content={
                "error": "DEPRECATED",
                "message": "RAG strategy settings moved to provider_clean system",
                "alternatives": [
                    "GET /api/providers/services/embedding - Get embedding configuration",
                    "GET /api/providers/services/llm_primary - Get LLM configuration"
                ]
            }
        )
    else:
        return JSONResponse(
            status_code=410,
            content={
                "error": "DEPRECATED",
                "message": f"Category '{category}' settings moved to provider_clean system",
                "alternatives": [
                    "GET /api/providers/services/backend - List all services",
                    "GET /api/providers/api-keys/providers - List active providers"
                ]
            }
        )


@router.post("/credentials", deprecated=True)
async def create_credential():
    """DEPRECATED: Use /api/providers/api-keys instead."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED", 
            "message": "Credential creation moved to provider_clean system",
            "alternatives": [
                "POST /api/providers/api-keys - Set provider API keys",
                "POST /api/providers/models/sync - Configure service models"
            ]
        }
    )


@router.get("/credential/{key}", deprecated=True)
async def get_credential(key: str):
    """DEPRECATED: Use provider_clean API endpoints instead."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED",
            "message": f"Individual credential access for '{key}' deprecated",
            "alternatives": [
                "Use environment variables for simple settings",
                "Use provider_clean API for provider configurations"
            ]
        }
    )


@router.put("/credential/{key}", deprecated=True)
async def update_credential(key: str):
    """DEPRECATED: Use provider_clean API endpoints instead."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED",
            "message": f"Credential updates for '{key}' moved to provider_clean system",
            "alternatives": [
                "POST /api/providers/api-keys - Update provider API keys",
                "Use environment variables for simple settings"
            ]
        }
    )


@router.delete("/credential/{key}", deprecated=True)
async def delete_credential(key: str):
    """DEPRECATED: Use provider_clean API endpoints instead."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED",
            "message": f"Credential deletion for '{key}' moved to provider_clean system",
            "alternatives": [
                "DELETE /api/providers/api-keys/{provider} - Remove provider API keys"
            ]
        }
    )


@router.post("/initialize-credentials", deprecated=True)
async def initialize_credentials_endpoint():
    """DEPRECATED: Provider clean system initializes automatically."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "DEPRECATED",
            "message": "Manual credential initialization no longer needed",
            "note": "Provider clean system initializes automatically on startup"
        }
    )


@router.get("/database/metrics")
async def database_metrics():
    """Get database metrics - works with any database system."""
    return {
        "status": "healthy",
        "message": "Database metrics available through provider_clean system",
        "note": "This endpoint provides basic status only"
    }


@router.get("/health")
async def settings_health():
    """Settings health check - provider_clean system status."""
    return {
        "status": "healthy",
        "system": "provider_clean",
        "message": "Settings managed by provider_clean system",
        "endpoints": [
            "/api/providers/services/backend",
            "/api/providers/api-keys/providers"
        ]
    }