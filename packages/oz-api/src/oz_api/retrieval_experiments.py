from __future__ import annotations

import hashlib
import os


def retrieval_variant(fingerprint: str = "") -> str:
    forced = os.environ.get("OZ_RETRIEVAL_VARIANT", "").strip()
    if forced:
        return forced
    raw = os.environ.get("OZ_RETRIEVAL_AB", "").strip()
    if not raw:
        return "control"
    variants = parse_variants(raw)
    if not variants:
        return "control"
    bucket = stable_bucket(fingerprint or "anonymous")
    cumulative = 0
    for name, percent in variants:
        cumulative += percent
        if bucket < cumulative:
            return name
    return variants[-1][0]


def rerank_enabled(variant: str) -> bool:
    return variant.lower() not in {"no_rerank", "rerank_off", "fts_only"}


def parse_variants(raw: str) -> list[tuple[str, int]]:
    variants: list[tuple[str, int]] = []
    for item in raw.split(","):
        if not item.strip():
            continue
        name, _, percent = item.partition(":")
        try:
            value = int(percent)
        except ValueError:
            continue
        if name.strip() and value > 0:
            variants.append((name.strip(), value))
    return variants


def stable_bucket(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % 100

