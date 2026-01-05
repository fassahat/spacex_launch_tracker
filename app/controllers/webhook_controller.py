"""Webhook management API endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.services.webhook_manager import (
    add_webhook,
    get_webhooks,
    delete_webhook
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    """Request model for creating a webhook."""
    url: HttpUrl
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response model for webhook."""
    id: int
    url: str
    description: Optional[str]
    active: bool
    created_at: str


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(webhook: WebhookCreate):
    """
    Register a new webhook for launch notifications.

    The webhook will receive POST requests when new launches are detected.
    """
    result = add_webhook(str(webhook.url), webhook.description)
    return result


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(active_only: bool = False):
    """List all registered webhooks."""
    return get_webhooks(active_only=active_only)


@router.delete("/{webhook_id}")
def remove_webhook(webhook_id: int):
    """Delete a webhook subscription."""
    success = delete_webhook(webhook_id)
    if success:
        return {"message": f"Webhook {webhook_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Webhook not found")
