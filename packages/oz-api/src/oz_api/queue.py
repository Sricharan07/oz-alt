from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from oz_api.storage import RegistryStorage


def enqueue_crawler_job(storage: RegistryStorage, payload: dict[str, Any]) -> dict[str, Any]:
    event = crawler_job_event(payload)
    missing = missing_required_crawler_fields(event)
    if missing:
        raise ValueError(f"missing crawler job fields: {', '.join(missing)}")
    message_id = send_sqs_message(event)
    if message_id:
        event["queue_message_id"] = message_id
        event["queue_backend"] = "sqs"
    else:
        event["queue_backend"] = "local"
    storage.append_admin_event("crawler_jobs", event)
    return event


def crawler_job_event(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": now(),
        "status": "queued",
        "library_name": payload.get("library_name") or payload.get("library"),
        "vendor": payload.get("vendor") or payload.get("vendor_hint"),
        "source_url": payload.get("source_url") or payload.get("source_url_hint"),
        "version": payload.get("version") or "latest",
        "max_pages": payload.get("max_pages"),
        "fetcher": payload.get("fetcher"),
        "concurrent_requests": payload.get("concurrent_requests"),
        "download_delay": payload.get("download_delay"),
        "robots_txt": payload.get("robots_txt"),
    }


def missing_required_crawler_fields(event: dict[str, Any]) -> list[str]:
    required = ["vendor", "library_name", "source_url"]
    return [field for field in required if not event.get(field)]


def send_sqs_message(event: dict[str, Any]) -> str | None:
    queue_url = os.environ.get("OZ_CRAWLER_QUEUE_URL")
    if not queue_url:
        return None
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    response = boto3.client("sqs").send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(strip_empty_values(event), sort_keys=True),
    )
    message_id = response.get("MessageId")
    return str(message_id) if message_id else None


def strip_empty_values(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if value is not None and value != ""}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
