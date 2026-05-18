#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.auth_store import AuthStore  # noqa: E402


def main() -> int:
    store = AuthStore.from_env()
    if store is None:
        raise SystemExit("OZ_DATABASE_URL or DATABASE_URL is required")
    retention_days = int(os.environ.get("OZ_AUDIT_RETENTION_DAYS", "365"))
    limit = int(os.environ.get("OZ_AUDIT_EXPORT_LIMIT", "100000"))
    bucket = os.environ.get("OZ_AUDIT_EXPORT_BUCKET") or os.environ.get("OZ_PACKS_BUCKET")
    prefix = os.environ.get("OZ_AUDIT_EXPORT_PREFIX", "audit-exports").strip("/")
    if not bucket:
        raise SystemExit("OZ_AUDIT_EXPORT_BUCKET or OZ_PACKS_BUCKET is required")

    run_id = start_run(store, retention_days)
    try:
        auth_rows = old_rows(store, "auth_audit_logs", retention_days, limit)
        admin_rows = old_rows(store, "admin_action_logs", retention_days, limit)
        if not auth_rows and not admin_rows:
            finish_run(store, run_id, "pruned", None, 0, 0)
            print("audit retention ok: no expired rows")
            return 0
        export_key = export_rows(bucket, prefix, auth_rows, admin_rows)
        mark_exported(store, run_id, export_key, len(auth_rows), len(admin_rows))
        delete_rows(store, "auth_audit_logs", [int(row["id"]) for row in auth_rows])
        delete_rows(store, "admin_action_logs", [int(row["id"]) for row in admin_rows])
        finish_run(store, run_id, "pruned", export_key, len(auth_rows), len(admin_rows))
        print(f"audit retention ok: s3://{bucket}/{export_key} auth={len(auth_rows)} admin={len(admin_rows)}")
        return 0
    except Exception as exc:
        fail_run(store, run_id, str(exc))
        raise


def start_run(store: AuthStore, retention_days: int) -> int:
    row = store.one(
        "insert into audit_retention_runs (status, retention_days) values ('started', :retention_days) returning id",
        {"retention_days": retention_days},
    )
    if not row:
        raise RuntimeError("failed to create audit retention run")
    return int(row["id"])


def old_rows(store: AuthStore, table: str, retention_days: int, limit: int) -> list[dict[str, Any]]:
    return store.execute(
        f"""
        select *
        from {table}
        where created_at < now() - make_interval(days => :retention_days)
        order by id asc
        limit :limit
        """,
        {"retention_days": retention_days, "limit": limit},
    )


def export_rows(bucket: str, prefix: str, auth_rows: list[dict[str, Any]], admin_rows: list[dict[str, Any]]) -> str:
    import boto3  # type: ignore

    now = datetime.now(timezone.utc)
    key = f"{prefix}/{now:%Y/%m/%d}/audit-{now:%Y%m%dT%H%M%SZ}.jsonl.gz"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl.gz") as tmp:
        path = Path(tmp.name)
    try:
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            for table, rows in (("auth_audit_logs", auth_rows), ("admin_action_logs", admin_rows)):
                for row in rows:
                    handle.write(json.dumps({"table": table, "row": row}, default=str, sort_keys=True) + "\n")
        boto3.client("s3", **s3_client_kwargs()).upload_file(str(path), bucket, key)
    finally:
        path.unlink(missing_ok=True)
    return key


def mark_exported(store: AuthStore, run_id: int, export_key: str, auth_count: int, admin_count: int) -> None:
    store.execute(
        """
        update audit_retention_runs
        set status = 'exported', export_key = :export_key, auth_rows = :auth_rows, admin_rows = :admin_rows
        where id = :id
        """,
        {"id": run_id, "export_key": export_key, "auth_rows": auth_count, "admin_rows": admin_count},
    )


def finish_run(store: AuthStore, run_id: int, status: str, export_key: str | None, auth_count: int, admin_count: int) -> None:
    store.execute(
        """
        update audit_retention_runs
        set status = :status,
            export_key = coalesce(:export_key, export_key),
            auth_rows = :auth_rows,
            admin_rows = :admin_rows,
            finished_at = now()
        where id = :id
        """,
        {"id": run_id, "status": status, "export_key": export_key, "auth_rows": auth_count, "admin_rows": admin_count},
    )


def fail_run(store: AuthStore, run_id: int, error: str) -> None:
    store.execute(
        "update audit_retention_runs set status = 'failed', finished_at = now(), last_error = :error where id = :id",
        {"id": run_id, "error": error[:2000]},
    )


def delete_rows(store: AuthStore, table: str, ids: list[int]) -> None:
    if not ids:
        return
    placeholders = ", ".join(f":id_{index}" for index, _ in enumerate(ids))
    parameters = {f"id_{index}": value for index, value in enumerate(ids)}
    store.execute(f"delete from {table} where id in ({placeholders})", parameters)


def s3_client_kwargs() -> dict[str, Any]:
    endpoint = os.environ.get("OZ_S3_ENDPOINT_URL") or os.environ.get("AWS_ENDPOINT_URL_S3")
    return {"endpoint_url": endpoint} if endpoint else {}


if __name__ == "__main__":
    raise SystemExit(main())
