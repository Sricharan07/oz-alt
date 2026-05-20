from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
from urllib import request

from oz_api.retrieval_context import openai_api_key_from_env

LOGGER = logging.getLogger(__name__)


def maybe_enrich_recipe(recipe: Any, evidence: list[dict[str, Any]]) -> Any:
    """Optionally rewrite a recipe into a compact implementation packet.

    This is deliberately off by default. When enabled, the model receives only
    source evidence and the result is accepted only if every API-like token is
    present in the evidence. Unsupported generations are discarded.
    """

    if not llm_enabled() or not evidence:
        return recipe
    payload = llm_payload(recipe, evidence)
    result = call_openai(payload)
    if not result:
        return recipe
    if not grounded_generation(result, evidence):
        LOGGER.warning("discarded ungrounded recipe enrichment for %s", getattr(recipe, "recipe_key", "unknown"))
        return recipe
    try:
        from dataclasses import replace

        content = str(result.get("content") or getattr(recipe, "content"))
        code = str(result.get("code") or getattr(recipe, "code") or "") or None
        info = str(result.get("info") or getattr(recipe, "info") or "")
        return replace(recipe, content=content, code=code, info=info, metadata_json={**getattr(recipe, "metadata_json"), "llm_enriched": True, "llm_model": llm_model()})
    except Exception:
        return recipe


def llm_enabled() -> bool:
    return os.environ.get("OZ_RECIPE_LLM_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def llm_model() -> str:
    return os.environ.get("OZ_RECIPE_LLM_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def openai_api_key() -> str:
    return openai_api_key_from_env() or (os.environ.get("OZ_OPENAI_API_KEY") or "").strip()


def llm_payload(recipe: Any, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    schema = {
        "name": "oz_grounded_recipe",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "content": {"type": "string"},
                "code": {"type": "string"},
                "info": {"type": "string"},
            },
            "required": ["content", "code", "info"],
        },
    }
    instructions = (
        "Write JSON for a compact source-backed implementation packet for a coding agent. "
        "Use only the provided evidence. Do not invent APIs, classes, methods, params, URLs, env vars, or model names. "
        "If evidence is incomplete, say exactly what is missing in info. Keep code minimal and runnable when evidence supports it."
    )
    return {
        "model": llm_model(),
        "input": [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "recipe": {
                            "title": getattr(recipe, "title", ""),
                            "task_kind": getattr(recipe, "task_kind", ""),
                            "content": getattr(recipe, "content", ""),
                            "code": getattr(recipe, "code", ""),
                            "info": getattr(recipe, "info", ""),
                        },
                        "evidence": evidence,
                    },
                    ensure_ascii=False,
                )[:24000],
            },
        ],
        "text": {"format": {"type": "json_schema", "name": schema["name"], "schema": schema["schema"], "strict": True}},
        "temperature": 0.1,
        "max_output_tokens": int(os.environ.get("OZ_RECIPE_LLM_MAX_OUTPUT_TOKENS", "900")),
    }


def call_openai(payload: dict[str, Any]) -> dict[str, Any] | None:
    key = openai_api_key()
    if not key:
        return None
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(os.environ.get("OZ_RECIPE_LLM_TIMEOUT_SECONDS", "20"))) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        LOGGER.warning("recipe LLM enrichment failed: %s", exc)
        return None
    text = extract_response_text(parsed)
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def extract_response_text(parsed: dict[str, Any]) -> str:
    if isinstance(parsed.get("output_text"), str):
        return parsed["output_text"]
    output = parsed.get("output")
    if not isinstance(output, list):
        return ""
    parts = []
    for item in output:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def grounded_generation(result: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    evidence_text = "\n".join(str(item.get("content") or "") for item in evidence)
    evidence_compact = compact(evidence_text)
    generated = "\n".join(str(result.get(key) or "") for key in ("content", "code", "info"))
    for token in api_tokens(generated):
        compact_token = compact(token)
        if len(compact_token) >= 4 and compact_token not in evidence_compact:
            return False
    return True


def api_tokens(text: str) -> set[str]:
    output = set(re.findall(r"\b[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?\b", text))
    output.update(re.findall(r"\b[a-z_][a-z0-9_]*\s*\(", text))
    output.update(re.findall(r"\b[A-Z_]{3,}\b", text))
    return {token.strip("(") for token in output if token not in {"JSON", "HTTP", "URL", "API"}}


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
