"""Settings endpoints — manage API keys and system configuration (superuser only)."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_superuser
from app.core.config import settings

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_active_superuser)],
)


def _mask_key(key: str) -> str:
    """Return a masked version of an API key for display purposes."""
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


class ApiKeyStatus(BaseModel):
    os_api_key: str
    here_api_key: str
    mapillary_token: str
    os_configured: bool
    here_configured: bool
    mapillary_configured: bool


class ApiKeyUpdate(BaseModel):
    os_api_key: str | None = None
    here_api_key: str | None = None
    mapillary_token: str | None = None


@router.get("/api-keys", response_model=ApiKeyStatus)
def get_api_key_status() -> Any:
    """
    Get the current status of configured API keys.
    Keys are masked for security — only first/last 4 chars shown.
    """
    return ApiKeyStatus(
        os_api_key=_mask_key(settings.OS_API_KEY),
        here_api_key=_mask_key(settings.HERE_API_KEY),
        mapillary_token=_mask_key(settings.MAPILLARY_TOKEN),
        os_configured=bool(settings.OS_API_KEY),
        here_configured=bool(settings.HERE_API_KEY),
        mapillary_configured=bool(settings.MAPILLARY_TOKEN),
    )


@router.put("/api-keys", response_model=ApiKeyStatus)
def update_api_keys(keys: ApiKeyUpdate) -> Any:
    """
    Update API keys at runtime. Only non-null fields are updated.
    Changes persist in memory for the current server process.
    To persist across restarts, also update the .env file.
    """
    if keys.os_api_key is not None:
        settings.OS_API_KEY = keys.os_api_key
    if keys.here_api_key is not None:
        settings.HERE_API_KEY = keys.here_api_key
    if keys.mapillary_token is not None:
        settings.MAPILLARY_TOKEN = keys.mapillary_token

    return ApiKeyStatus(
        os_api_key=_mask_key(settings.OS_API_KEY),
        here_api_key=_mask_key(settings.HERE_API_KEY),
        mapillary_token=_mask_key(settings.MAPILLARY_TOKEN),
        os_configured=bool(settings.OS_API_KEY),
        here_configured=bool(settings.HERE_API_KEY),
        mapillary_configured=bool(settings.MAPILLARY_TOKEN),
    )
