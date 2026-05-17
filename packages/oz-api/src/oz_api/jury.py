from __future__ import annotations

import json
import os
from typing import Any
from urllib import request


def jury_requested() -> bool:
    return os.environ.get("OZ_EVAL_JURY", "").strip().lower() in {"1", "true", "yes", "on"}


def jury_required() -> bool:
    return os.environ.get("OZ_EVAL_REQUIRE_JURY", "").strip().lower() in {"1", "true", "yes", "on"}


def judge_search_check(check: dict[str, Any], paths: list[str], contents: list[str]) -> dict[str, Any]:
    api_key = jury_api_key()
    endpoint = os.environ.get("OZ_EVAL_JURY_URL", "").strip() or "https://api.openai.com/v1/chat/completions"
    model = os.environ.get("OZ_EVAL_JURY_MODEL", "").strip() or "gpt-4o-mini"
    if not api_key:
        raise RuntimeError("jury eval requires OZ_EVAL_JURY_API_KEY or OPENAI_API_KEY")
    snippets = [
        {"path": path, "content": contents[index][:2500] if index < len(contents) else ""}
        for index, path in enumerate(paths[:5])
    ]
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Score documentation search results for a coding agent. Return JSON with "
                    "relevance, correctness, clarity, score, and reason. Scores must be 0 to 1."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "query": check.get("query"),
                        "expected_files": check.get("expected_files", []),
                        "must_include": check.get("must_include", []),
                        "must_not_include": check.get("must_not_include", []),
                        "results": snippets,
                    },
                    sort_keys=True,
                ),
            },
        ],
    }
    body = request_json(endpoint, payload, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    content = body.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(body, dict) else None
    parsed = json.loads(content) if isinstance(content, str) else {}
    return normalize_jury_result(parsed)


def normalize_jury_result(parsed: dict[str, Any]) -> dict[str, Any]:
    relevance = score_field(parsed, "relevance")
    correctness = score_field(parsed, "correctness")
    clarity = score_field(parsed, "clarity")
    score = score_field(parsed, "score")
    if score == 0 and any((relevance, correctness, clarity)):
        score = (relevance + correctness + clarity) / 3.0
    return {
        "relevance": round(relevance, 3),
        "correctness": round(correctness, 3),
        "clarity": round(clarity, 3),
        "score": round(score, 3),
        "reason": str(parsed.get("reason") or "")[:500] if isinstance(parsed, dict) else "",
    }


def score_field(payload: dict[str, Any], field: str) -> float:
    try:
        return max(0.0, min(float(payload.get(field) or 0), 1.0))
    except (TypeError, ValueError):
        return 0.0


def request_json(endpoint: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with request.urlopen(req, timeout=float(os.environ.get("OZ_EVAL_JURY_TIMEOUT_SECONDS", "45"))) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body if isinstance(body, dict) else {}


def jury_api_key() -> str:
    return (
        os.environ.get("OZ_EVAL_JURY_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OZ_OPENAI_API_KEY")
        or ""
    ).strip()
