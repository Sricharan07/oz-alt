from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.storage import RegistryStorage  # noqa: E402


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    storage = RegistryStorage.from_env(Path(os.environ.get("OZ_REPO_ROOT", ".")).resolve())
    started = 0
    for record in event.get("Records", []):
        job = parse_body(record.get("body"))
        task_arns = run_fargate_task(job)
        storage.append_admin_event(
            "crawler_jobs",
            {
                "status": "fargate_started",
                "vendor": job.get("vendor") or job.get("vendor_hint"),
                "library_name": job.get("library_name") or job.get("library"),
                "source_url": job.get("source_url") or job.get("source_url_hint"),
                "task_arns": task_arns,
            },
        )
        started += 1
    return {"started": started}


def run_fargate_task(job: dict[str, Any]) -> list[str]:
    import boto3  # type: ignore

    cluster = required_env("OZ_FARGATE_CLUSTER")
    task_definition = required_env("OZ_FARGATE_TASK_DEFINITION")
    subnets = csv_env("OZ_FARGATE_SUBNETS")
    security_group = required_env("OZ_FARGATE_SECURITY_GROUP")
    container_name = os.environ.get("OZ_FARGATE_CONTAINER", "CrawlerContainer")
    capacity_provider = os.environ.get("OZ_FARGATE_CAPACITY_PROVIDER", "FARGATE_SPOT")

    response = boto3.client("ecs").run_task(
        cluster=cluster,
        taskDefinition=task_definition,
        capacityProviderStrategy=[{"capacityProvider": capacity_provider, "weight": 1}],
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": [security_group],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": container_name,
                    "environment": [
                        {
                            "name": "OZ_CRAWLER_JOB",
                            "value": json.dumps(job, sort_keys=True),
                        }
                    ],
                }
            ]
        },
    )
    failures = response.get("failures") or []
    if failures:
        raise RuntimeError(f"failed to start Fargate crawler task: {failures}")
    return [str(task["taskArn"]) for task in response.get("tasks", []) if task.get("taskArn")]


def parse_body(body: Any) -> dict[str, Any]:
    if isinstance(body, dict):
        return body
    parsed = json.loads(str(body or "{}"))
    if not isinstance(parsed, dict):
        raise RuntimeError("crawler DLQ message body must be a JSON object")
    return parsed


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def csv_env(name: str) -> list[str]:
    values = [value.strip() for value in required_env(name).split(",") if value.strip()]
    if not values:
        raise RuntimeError(f"{name} must contain at least one value")
    return values
