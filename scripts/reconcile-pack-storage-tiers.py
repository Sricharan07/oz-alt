#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.auth_store import AuthStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify Oz packs as hot/cold and reconcile S3 object tags.")
    parser.add_argument("--cold-after-days", type=int, default=int(os.environ.get("OZ_COLD_PACK_AFTER_DAYS", "30")))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    store = AuthStore.from_env()
    if store is None:
        raise SystemExit("OZ_DATABASE_URL or DATABASE_URL is required")
    bucket = os.environ.get("OZ_PACKS_BUCKET")
    rows = classify_packs(store, args.cold_after_days, dry_run=args.dry_run)
    if bucket:
        tag_s3_packs(bucket, rows, dry_run=args.dry_run)
    print(f"pack tiers reconciled: rows={len(rows)} bucket={bucket or 'none'} dry_run={args.dry_run}")
    return 0


def classify_packs(store: AuthStore, cold_after_days: int, *, dry_run: bool) -> list[dict[str, Any]]:
    rows = store.execute(
        """
        with latest_packs as (
          select distinct pb.id
          from pack_builds pb
          join libraries l on l.id = pb.library_id
          join refs r on r.library_id = l.id and r.channel = 'latest'
          join library_versions lv on lv.id = r.version_id
          where lv.version = pb.version
        ),
        classified as (
          select pb.id,
                 pb.pack_key,
                 case
                   when lp.id is not null then 'hot'
                   when coalesce(pb.last_downloaded_at, pb.created_at) < now() - make_interval(days => :cold_after_days) then 'cold'
                   else 'hot'
                 end as target_tier
          from pack_builds pb
          left join latest_packs lp on lp.id = pb.id
        )
        select id, pack_key, target_tier
        from classified
        order by id asc
        """,
        {"cold_after_days": cold_after_days},
    )
    if not dry_run:
        for row in rows:
            store.execute(
                "update pack_builds set storage_tier = :tier where id = :id",
                {"tier": row["target_tier"], "id": row["id"]},
            )
    return rows


def tag_s3_packs(bucket: str, rows: list[dict[str, Any]], *, dry_run: bool) -> None:
    import boto3  # type: ignore

    client = boto3.client("s3", **s3_client_kwargs())
    for row in rows:
        key = str(row.get("pack_key") or "").strip("/")
        if not key:
            continue
        tier = str(row.get("target_tier") or "hot")
        tags = {"oz-role": "pack", "oz-canonical": "true", "oz-storage-tier": tier}
        if dry_run:
            continue
        client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={"TagSet": [{"Key": key_, "Value": value} for key_, value in sorted(tags.items())]},
        )


def s3_client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    endpoint = os.environ.get("OZ_S3_ENDPOINT_URL") or os.environ.get("AWS_ENDPOINT_URL_S3")
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return kwargs


if __name__ == "__main__":
    raise SystemExit(main())
