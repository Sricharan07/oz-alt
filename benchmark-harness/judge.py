#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from harness import write_json


HARNESS = Path(__file__).resolve().parent
DEFAULT_MODELS = [
    "openai/gpt-5",
    "x-ai/grok-4",
    "deepseek/deepseek-v3.2-exp",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run optional multi-model judging over Oz benchmark run artifacts.")
    parser.add_argument("run_dir")
    parser.add_argument("--model", action="append", default=[], help="Judge model. Repeat for multiple models.")
    parser.add_argument("--api-base", default=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-packet-chars", type=int, default=30000)
    parser.add_argument("--provider-summary", action="append", default=[], help="Optional provider summary JSON to include.")
    parser.add_argument("--dry-run", action="store_true", help="Build judge prompts without calling a model.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"run directory not found: {run_dir}")
    models = args.model or DEFAULT_MODELS
    api_key = os.environ.get(args.api_key_env, "").strip()
    if not args.dry_run and not api_key:
        raise SystemExit(f"{args.api_key_env} is required, or pass --dry-run")

    provider_context = load_provider_context([Path(path) for path in args.provider_summary])
    case_dirs = sorted((run_dir / "cases").glob("*"))
    if not case_dirs:
        raise SystemExit(f"no case directories found under {run_dir / 'cases'}")

    results: list[dict[str, Any]] = []
    prompt_dir = run_dir / "judge_prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for index, case_dir in enumerate(case_dirs, start=1):
        packet_path = case_dir / "judge_packet.md"
        result_path = case_dir / "result.json"
        if not packet_path.exists() or not result_path.exists():
            continue
        case_result = json.loads(result_path.read_text(encoding="utf-8"))
        print(f"[{index}/{len(case_dirs)}] judge {case_result['case_id']}", file=sys.stderr, flush=True)
        prompt = build_prompt(packet_path, case_result, provider_context, max_chars=args.max_packet_chars)
        (prompt_dir / f"{case_result['case_id']}.md").write_text(prompt, encoding="utf-8")
        model_scores: list[dict[str, Any]] = []
        if not args.dry_run:
            for model in models:
                started = time.monotonic()
                score = call_judge_model(args.api_base, api_key, model, prompt, timeout=args.timeout)
                score["model"] = model
                score["latency_ms"] = int((time.monotonic() - started) * 1000)
                model_scores.append(score)
        result = {
            "case_id": case_result["case_id"],
            "library": case_result["library"],
            "query": case_result["query"],
            "dry_run": bool(args.dry_run),
            "models": models,
            "scores": model_scores,
            "majority": majority_score(model_scores),
            "prompt_path": str(prompt_dir / f"{case_result['case_id']}.md"),
        }
        results.append(result)
        write_json(run_dir / "judge_results.json", {"results": results, "summary": summarize(results)})

    payload = {"results": results, "summary": summarize(results)}
    write_json(run_dir / "judge_results.json", payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


def build_prompt(packet_path: Path, case_result: dict[str, Any], provider_context: str, *, max_chars: int) -> str:
    packet = packet_path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    oracle = load_oracle(case_result, packet_path.parent)
    parts = [
        "You are judging documentation context for a coding agent.",
        "",
        "Return strict JSON with these keys:",
        "- completeness: boolean",
        "- relevance: boolean",
        "- overall_score: integer 1-5",
        "- confidence: high|medium|low",
        "- expected_source_used: boolean",
        "- hallucinated_api: boolean",
        "- excessive_context: boolean",
        "- version_mismatch: boolean",
        "- reasoning: short string",
        "",
        "Judge whether the retrieved docs and agent evidence are enough to answer the coding task accurately.",
        "Reward exact source grounding and low-token sufficiency. Penalize irrelevant context, missing API details, and version drift.",
        "",
        "## Oz Judge Packet",
        "",
        packet,
    ]
    if oracle:
        parts.extend(["", "## Oracle", "", oracle[:10000]])
    if provider_context:
        parts.extend(["", "## External Provider Summaries", "", provider_context[:12000]])
    return "\n".join(parts).strip() + "\n"


def load_oracle(case_result: dict[str, Any], case_dir: Path) -> str:
    case_path = case_dir / "case.json"
    case = json.loads(case_path.read_text(encoding="utf-8")) if case_path.exists() else {}
    oracle = case.get("oracle") or case.get("expected_answer") or ""
    if oracle:
        return str(oracle)
    oracle_path = str(case.get("oracle_path") or "")
    if not oracle_path:
        return ""
    path = Path(oracle_path)
    if not path.is_absolute():
        path = HARNESS / oracle_path
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def load_provider_context(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = {key: value for key, value in data.items() if key not in {"results"}}
        chunks.append(f"### {path.name}\n\n```json\n{json.dumps(summary, indent=2, sort_keys=True)}\n```")
    return "\n\n".join(chunks)


def call_judge_model(api_base: str, api_key: str, model: str, prompt: str, *, timeout: int) -> dict[str, Any]:
    url = api_base.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict evaluator. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tryoz.dev",
            "X-Title": "Oz Benchmark Harness",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {
            "error": exc.read().decode("utf-8", "replace")[:2000],
            "status": exc.code,
            "completeness": False,
            "relevance": False,
            "overall_score": 0,
            "confidence": "low",
            "reasoning": "judge API request failed",
        }
    content = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "")
    parsed = parse_json_object(content)
    return normalize_score(parsed)


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {"reasoning": text[:500]}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {"reasoning": text[:500]}


def normalize_score(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "completeness": bool(value.get("completeness")),
        "relevance": bool(value.get("relevance")),
        "overall_score": clamp_int(value.get("overall_score"), 0, 5),
        "confidence": str(value.get("confidence") or "low"),
        "expected_source_used": bool(value.get("expected_source_used")),
        "hallucinated_api": bool(value.get("hallucinated_api")),
        "excessive_context": bool(value.get("excessive_context")),
        "version_mismatch": bool(value.get("version_mismatch")),
        "reasoning": str(value.get("reasoning") or "")[:1200],
    }


def majority_score(scores: list[dict[str, Any]]) -> dict[str, Any]:
    if not scores:
        return {
            "passed": None,
            "completeness": None,
            "relevance": None,
            "avg_overall_score": 0.0,
            "judge_count": 0,
        }
    complete = sum(1 for score in scores if score.get("completeness"))
    relevant = sum(1 for score in scores if score.get("relevance"))
    threshold = len(scores) // 2 + 1
    avg_score = round(sum(float(score.get("overall_score") or 0) for score in scores) / len(scores), 4)
    return {
        "passed": complete >= threshold and relevant >= threshold,
        "completeness": complete >= threshold,
        "relevance": relevant >= threshold,
        "avg_overall_score": avg_score,
        "judge_count": len(scores),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    judged = [row for row in results if row.get("majority", {}).get("judge_count", 0)]
    if not judged:
        return {"case_count": len(results), "judged_count": 0, "pass_rate": 0.0, "avg_overall_score": 0.0}
    pass_rate = sum(1 for row in judged if row["majority"].get("passed")) / len(judged)
    avg_score = sum(float(row["majority"].get("avg_overall_score") or 0) for row in judged) / len(judged)
    return {
        "case_count": len(results),
        "judged_count": len(judged),
        "pass_rate": round(pass_rate, 4),
        "avg_overall_score": round(avg_score, 4),
    }


def clamp_int(value: Any, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return low
    return max(low, min(high, parsed))


if __name__ == "__main__":
    raise SystemExit(main())
