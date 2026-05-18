#!/usr/bin/env bash
set -euo pipefail

BUCKET="${1:-${OZ_PACKS_BUCKET:-}}"
PACK_PREFIX="${OZ_PACK_PREFIX:-packs}"
NONCANONICAL_DAYS="${OZ_NONCANONICAL_PACK_RETENTION_DAYS:-90}"
ARTIFACT_DAYS="${OZ_ARTIFACT_RETENTION_DAYS:-30}"
ABORT_MULTIPART_DAYS="${OZ_ABORT_MULTIPART_DAYS:-7}"
COLD_TRANSITION_DAYS="${OZ_COLD_PACK_TRANSITION_DAYS:-30}"

if [ -z "$BUCKET" ]; then
  echo "usage: scripts/apply-s3-lifecycle.sh <bucket>" >&2
  echo "or set OZ_PACKS_BUCKET" >&2
  exit 2
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

python3 - "$tmp" "$PACK_PREFIX" "$NONCANONICAL_DAYS" "$ARTIFACT_DAYS" "$ABORT_MULTIPART_DAYS" "$COLD_TRANSITION_DAYS" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
pack_prefix = sys.argv[2].strip("/") + "/"
noncanonical_days = int(sys.argv[3])
artifact_days = int(sys.argv[4])
abort_days = int(sys.argv[5])
cold_transition_days = int(sys.argv[6])

document = {
    "Rules": [
        {
            "ID": "expire-noncanonical-oz-packs",
            "Status": "Enabled",
            "Filter": {
                "And": {
                    "Prefix": pack_prefix,
                    "Tags": [{"Key": "oz-canonical", "Value": "false"}],
                }
            },
            "Expiration": {"Days": noncanonical_days},
        },
        {
            "ID": "expire-crawl-artifacts",
            "Status": "Enabled",
            "Filter": {"Prefix": "artifacts/"},
            "Expiration": {"Days": artifact_days},
        },
        {
            "ID": "transition-cold-oz-packs",
            "Status": "Enabled",
            "Filter": {
                "And": {
                    "Prefix": pack_prefix,
                    "Tags": [{"Key": "oz-storage-tier", "Value": "cold"}],
                }
            },
            "Transitions": [{"Days": cold_transition_days, "StorageClass": "STANDARD_IA"}],
        },
        {
            "ID": "abort-incomplete-multipart-uploads",
            "Status": "Enabled",
            "Filter": {"Prefix": ""},
            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": abort_days},
        },
    ]
}
path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
PY

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration "file://$tmp"

echo "s3 lifecycle applied: bucket=$BUCKET pack_prefix=$PACK_PREFIX noncanonical_days=$NONCANONICAL_DAYS artifact_days=$ARTIFACT_DAYS"
