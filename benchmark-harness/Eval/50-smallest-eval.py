#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

import eval as base_eval


LIBRARY_ID = os.getenv("OZ_EVAL_LIBRARY_ID", "/smallest/py-sdk")
CTX7_ID = os.getenv("CTX7_ID", "/smallest-inc/smallest-python-sdk")
OZ_LIBRARY_NAME_DEFAULT = os.getenv("OZ_EVAL_LIBRARY_NAME_DEFAULT", "Smallest AI")
OZ_VERSION_HINT_DEFAULT = os.getenv("OZ_EVAL_VERSION_HINT_DEFAULT", "latest")
WINNER_VALUES = {"ours", "context7", "tie"}

# Current 20-query baseline (commented out for reference).
# QUERIES = [
#     "How do I install and initialize the Smallest AI Python SDK?",
#     "How do I authenticate with a Smallest API key in Python?",
#     "How do I synthesize speech with Waves using the Python SDK?",
#     "How do I stream text to speech audio with Waves in Python?",
#     "How do I use Atoms to build or run a voice agent?",
#     "What are the required parameters for a Waves text to speech request?",
#     "How do I choose or configure a voice/model for Smallest text to speech?",
#     "How do I save generated audio to a file in Python?",
#     "How do I handle errors from Smallest API calls in the Python SDK?",
#     "Show a complete minimal Python example that sends text to Smallest and plays or writes the audio output.",
#     "How do I install smallestai with a pinned major version?",
#     "How do I configure API credentials without hardcoding secrets?",
#     "How do I select a Waves model for low-latency speech generation?",
#     "How do I configure language settings for an Atoms agent?",
#     "How do I create and update an Atoms agent template?",
#     "How do I create a knowledge base and attach files to it?",
#     "How do I run a voice session with an existing Atoms agent?",
#     "How do I capture and inspect response metadata from SDK calls?",
#     "How do I retry transient API failures in Python?",
#     "How do I structure a production-ready Smallest client wrapper?",
# ]

BASE_QUERIES = [
    "How do I install and initialize the Smallest AI Python SDK?",
    "How do I pin the Smallest AI SDK to a safe version range in requirements.txt?",
    "How do I authenticate using SMALLEST_API_KEY with the Python SDK?",
    "How do I initialize AtomsClient with default configuration?",
    "How do I initialize AtomsClient with a custom API host endpoint?",
    "How do I verify my Smallest API key is valid using a lightweight API call?",
    "What environment variables are required to run Smallest Python examples locally?",
    "How do I generate speech with Waves from plain text in Python?",
    "How do I stream Waves audio output chunk-by-chunk in Python?",
    "How do I save generated Waves audio to a WAV or MP3 file?",
    "How do I choose a Waves model for quality vs latency tradeoffs?",
    "How do I choose and set voiceId for Waves synthesis requests?",
    "What are the required fields for a Waves text-to-speech request body?",
    "How do I pass optional synthesis controls like speed, consistency, or enhancement?",
    "How do I handle long input text when generating speech with Waves?",
    "How do I split long text into safe chunks and stitch audio outputs together?",
    "How do I detect and recover from failed Waves generation requests?",
    "How do I log request IDs and response metadata for Waves debugging?",
    "How do I create a new Atoms voice agent in Python?",
    "How do I list available Atoms agents and fetch details for one agent?",
    "How do I update an existing Atoms agent configuration?",
    "How do I delete or disable an Atoms agent safely?",
    "How do I configure language settings when creating an Atoms agent?",
    "How do I configure synthesizer voice settings for an Atoms agent?",
    "How do I configure the SLM model for an Atoms agent?",
    "How do I create and retrieve agent templates using the Atoms API?",
    "How do I apply an agent template when creating a new agent?",
    "How do I create a knowledge base for an Atoms agent?",
    "How do I upload a PDF file into a Smallest knowledge base?",
    "How do I ingest documentation URLs into a Smallest knowledge base?",
    "How do I link a knowledge base to an Atoms agent at creation time?",
    "How do I update an agent to attach or detach knowledge bases?",
    "How do I inspect which knowledge base documents were ingested successfully?",
    "How do I handle file upload errors when adding docs to a knowledge base?",
    "How do I start a conversation/session with an Atoms agent?",
    "How do I send user turns and receive assistant responses from Atoms?",
    "How do I stream Atoms responses in real time for a voice experience?",
    "How do I pass conversation context or memory between Atoms turns?",
    "How do I terminate or clean up an active Atoms session?",
    "How do I implement retries with backoff for Smallest API rate limits?",
    "How do I classify Smallest API errors into retryable vs non-retryable?",
    "How do I add timeout controls to Smallest Python SDK requests?",
    "How do I build a reusable Smallest client wrapper class for production?",
    "How do I structure async usage for Smallest calls in a FastAPI service?",
    "How do I secure Smallest credentials in CI/CD and deployment environments?",
    "How do I write unit tests for code that calls Smallest APIs?",
    "How do I mock Atoms and Waves API calls for local integration tests?",
    "How do I measure end-to-end latency for a text-to-speech pipeline with Smallest?",
    "How do I compare direct Waves usage versus Atoms-managed synthesis in one workflow?",
    "Show a complete production-style Python example that authenticates, creates or loads an agent, and generates voice output.",
]

ONE_SHOT_AGENT_QUERIES = [
    "Build a complete Python CLI that reads SMALLEST_API_KEY, accepts text and output path arguments, calls Waves text-to-speech, and writes a WAV file.",
    "Build a FastAPI /tts endpoint that accepts text, calls Smallest Waves from Python, and returns audio bytes with the correct media type.",
    "Build a minimal Atoms agent provisioning script that creates an agent, sets language, synthesizer voice, SLM model, and prints the new agent id.",
    "Build a script that creates a Smallest knowledge base, uploads a local PDF, ingests one documentation URL, and attaches that knowledge base to an Atoms agent.",
    "Build a reusable SmallestClient class that initializes AtomsClient from environment variables and exposes create_agent, get_org, and synthesize_speech helpers.",
    "Build pytest tests for a Smallest wrapper by mocking AtomsClient methods and asserting create_agent is called with the correct request body.",
    "Build a production-safe Waves synthesis function with timeout, retry/backoff for 429/5xx, non-retry for 401/403, and request id logging if available.",
    "Build a Python streaming TTS example that consumes a generator of text chunks and writes streamed audio frames to a wav file.",
    "Build an Atoms conversation/session example that starts a session, sends a user turn, receives the agent response, and cleans up the session.",
    "Build a migration checklist for moving from direct Waves TTS calls to Atoms-managed voice synthesis, including what code changes and config fields are required.",
    "Given only the docs, write the exact imports and initialization code for AtomsClient default config and custom Configuration host config.",
    "Given only the docs, write the exact imports and method calls for creating, listing, updating, and deleting Atoms agents.",
    "Given only the docs, write the exact imports and method calls for creating a knowledge base, uploading a file, and checking ingestion status.",
    "Given only the docs, write the exact request fields for Waves text-to-speech including text, voice id, model, output format, sample rate, speed, and enhancement controls.",
    "Given only the docs, write the smallest working example that validates credentials by calling a lightweight Smallest API method.",
    "Build a local example app that uses AtomsApp or the Smallest agent server primitives with one tool function and an OpenAI-backed response node.",
    "Build a script that loads configuration from .env, avoids hardcoded secrets, validates required variables, and initializes both Atoms and Waves clients.",
    "Build an example that logs structured metadata for every Smallest call: operation name, agent id or voice id, latency, status, and request id when present.",
    "Build a robust upload flow for a knowledge base PDF that handles missing file, unsupported file type, API upload failure, and successful document id response.",
    "Build a complete README-style quickstart for a new developer integrating Smallest AI in Python, from install to first Atoms agent and first Waves TTS output.",
]

QUERIES = BASE_QUERIES + ONE_SHOT_AGENT_QUERIES
FAILURE_TAG_VALUES = {
    "wrong_product",
    "wrong_api",
    "missing_code",
    "missing_imports",
    "missing_params",
    "missing_return_shape",
    "missing_setup",
    "malformed_code",
    "fragmented_snippet",
    "generic_advice",
    "weak_source",
    "too_verbose",
    "too_sparse",
    "contradictory",
    "not_one_shot",
}


def _coerce_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    if score < 0:
        return 0.0
    if score > 10:
        return 10.0
    return score


def _winner_from_scores(ours: float, context7: float) -> str:
    if ours > context7:
        return "ours"
    if context7 > ours:
        return "context7"
    return "tie"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _coerce_string_list(value: Any, *, allowed: set[str] | None = None, max_items: int = 8) -> list[str]:
    if value is None:
        return []
    raw_items: list[Any]
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = [value]
    items: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        text = str(raw or "").strip()
        if not text:
            continue
        if allowed is not None:
            text = text.lower().replace(" ", "_").replace("-", "_")
            if text not in allowed:
                continue
        if text in seen:
            continue
        seen.add(text)
        items.append(text)
        if len(items) >= max_items:
            break
    return items


def _normalize_judge_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {"ours": {}, "context7": {}}
    for side in ("ours", "context7"):
        raw_side = payload.get(side) if isinstance(payload.get(side), dict) else {}
        for metric in base_eval.METRICS:
            normalized[side][metric] = _coerce_score(raw_side.get(metric))
        normalized[side]["one_shot_ready"] = _coerce_bool(raw_side.get("one_shot_ready"))
        normalized[side]["critical_gaps"] = _coerce_string_list(raw_side.get("critical_gaps"), max_items=8)
        normalized[side]["missing_apis"] = _coerce_string_list(raw_side.get("missing_apis"), max_items=8)
        normalized[side]["formatting_failures"] = _coerce_string_list(raw_side.get("formatting_failures"), max_items=8)
        normalized[side]["failure_tags"] = _coerce_string_list(
            raw_side.get("failure_tags"),
            allowed=FAILURE_TAG_VALUES,
            max_items=8,
        )

    winner_by_metric: dict[str, str] = {}
    raw_winners = payload.get("winner_by_metric") if isinstance(payload.get("winner_by_metric"), dict) else {}
    for metric in base_eval.METRICS:
        raw_value = str(raw_winners.get(metric) or "").strip().lower()
        if raw_value not in WINNER_VALUES:
            raw_value = _winner_from_scores(
                float(normalized["ours"][metric]),
                float(normalized["context7"][metric]),
            )
        winner_by_metric[metric] = raw_value

    overall_winner = str(payload.get("overall_winner") or "").strip().lower()
    if overall_winner not in WINNER_VALUES:
        overall_winner = winner_by_metric.get("overall") or _winner_from_scores(
            float(normalized["ours"]["overall"]),
            float(normalized["context7"]["overall"]),
        )

    summary = str(payload.get("summary") or "").strip()
    if not summary:
        summary = "Judge response was incomplete; fallback normalization was applied."

    return {
        "ours": normalized["ours"],
        "context7": normalized["context7"],
        "winner_by_metric": winner_by_metric,
        "overall_winner": overall_winner,
        "summary": summary,
    }


def summarize_one_shot(rows: list[dict[str, Any]]) -> dict[str, Any]:
    readiness = {"ours": 0, "context7": 0}
    failure_tags = {"ours": Counter(), "context7": Counter()}
    missing_apis = {"ours": Counter(), "context7": Counter()}
    for row in rows:
        judge = row.get("judge", {})
        for side in ("ours", "context7"):
            side_judge = judge.get(side, {}) if isinstance(judge.get(side), dict) else {}
            if side_judge.get("one_shot_ready"):
                readiness[side] += 1
            failure_tags[side].update(side_judge.get("failure_tags") or [])
            missing_apis[side].update(side_judge.get("missing_apis") or [])

    return {
        "one_shot_ready": readiness,
        "top_failure_tags": {
            side: [{"tag": tag, "count": count} for tag, count in counts.most_common(10)]
            for side, counts in failure_tags.items()
        },
        "top_missing_apis": {
            side: [{"api": api, "count": count} for api, count in counts.most_common(10)]
            for side, counts in missing_apis.items()
        },
    }


def _live_metric_line(side: str, judge: dict[str, Any]) -> str:
    payload = judge.get(side, {}) if isinstance(judge.get(side), dict) else {}
    return (
        f"overall={float(payload.get('overall') or 0):.1f} "
        f"rel={float(payload.get('relevance') or 0):.1f} "
        f"act={float(payload.get('actionability') or 0):.1f} "
        f"code={float(payload.get('code_utility') or 0):.1f} "
        f"src={float(payload.get('source_grounding') or 0):.1f} "
        f"one_shot={bool(payload.get('one_shot_ready'))}"
    )


def _live_tag_line(side: str, judge: dict[str, Any]) -> str:
    payload = judge.get(side, {}) if isinstance(judge.get(side), dict) else {}
    tags = ", ".join(payload.get("failure_tags") or []) or "none"
    gaps = "; ".join(payload.get("critical_gaps") or []) or "none"
    return f"tags={tags} | gaps={gaps}"


def _write_partial_report(
    path: Path,
    *,
    run_id: str,
    rows: list[dict[str, Any]],
    queries: list[str],
    model: str,
    mcp_url: str,
    library_name: str,
    version_hint: str,
    fallback_context_id: str | None,
) -> None:
    payload: dict[str, Any] = {
        "libraryId": LIBRARY_ID,
        "context7Id": CTX7_ID,
        "oz": {
            "mcpUrl": mcp_url,
            "libraryName": library_name,
            "versionHint": version_hint,
            "fallbackContextId": fallback_context_id,
            "tools": ["oz pull", "oz context"],
        },
        "runId": run_id,
        "partial": True,
        "completedQueries": len(rows),
        "totalQueries": len(queries),
        "queries": queries,
        "metrics": base_eval.METRICS,
        "model": model,
        "rubric": "strict_one_shot_coding_agent",
        "rows": rows,
    }
    if rows:
        payload["summary"] = base_eval.aggregate(rows)
        payload["oneShotSummary"] = summarize_one_shot(rows)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def judge_query(client: OpenAI, model: str, query: str, ours: str, context7: str) -> dict[str, Any]:
    prompt = f"""
You are a strict evaluator for documentation retrieval used by a coding agent.

The coding agent needs source-grounded context that helps it write correct code immediately.
Be harsh. Do not reward generic summaries, marketing prose, empty packet headings, or text that lacks concrete API usage.
Judge by the same standard as an autonomous coding benchmark: can a developer or agent implement the requested task from this retrieved context alone, without another lookup?

Query:
{query}

Output A (Oz CLI: oz pull -> oz context):
{ours}

Output B (Context7):
{context7}

Score both outputs from 1 to 10 on these metrics:
- relevance: directly answers the exact query, not adjacent concepts
- actionability: gives concrete implementation steps the agent can follow
- code_utility: includes correct imports, method names, parameters, and complete-enough snippets when the query is code-shaped
- token_efficiency: useful signal per token; short but useless is bad, verbose but precise can be good
- source_grounding: cites or clearly comes from official docs/source pages
- overall: how useful this is as context for an autonomous coding agent

Also decide:
- one_shot_ready: true only if the output contains enough concrete information for an agent to implement the task without another docs call.
- critical_gaps: short human-readable missing pieces, such as "missing AtomsClient import" or "no host configuration parameter".
- missing_apis: exact missing API/class/method/field names when inferable from the query or competing output.
- formatting_failures: code or formatting problems that would hurt copy/paste implementation.
- failure_tags: choose zero or more from:
  wrong_product, wrong_api, missing_code, missing_imports, missing_params,
  missing_return_shape, missing_setup, malformed_code, fragmented_snippet,
  generic_advice, weak_source, too_verbose, too_sparse, contradictory, not_one_shot.

Hard caps:
- If an output is an error, empty, or says evidence is unavailable, overall must be <= 2.
- If it has no concrete API/method/parameter information for a how-to query, overall must be <= 5.
- If it is relevant but missing code for a code-shaped query, code_utility must be <= 5.
- If it appears ungrounded or cannot be traced to source docs, source_grounding must be <= 5.
- If it retrieves the wrong product area, overall must be <= 3.
- If code blocks are malformed, fused with line numbers, or unsafe to copy/paste, code_utility must be <= 3.
- If an output lacks imports + client initialization for an SDK implementation query, one_shot_ready must be false.
- If a response is relevant but fragmented across snippets without enough glue to implement, one_shot_ready must be false.
- If the query asks for retries, timeouts, tests, deployment, or production behavior and the official retrieved docs do not contain those details, score honestly low instead of rewarding generic best practices.

Return strict JSON with this shape:
{{
  "ours": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0, "one_shot_ready": false, "critical_gaps": [], "missing_apis": [], "formatting_failures": [], "failure_tags": []}},
  "context7": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0, "one_shot_ready": false, "critical_gaps": [], "missing_apis": [], "formatting_failures": [], "failure_tags": []}},
  "winner_by_metric": {{"relevance": "ours|context7|tie", "actionability": "...", "code_utility": "...", "token_efficiency": "...", "source_grounding": "...", "overall": "..."}},
  "overall_winner": "ours|context7|tie",
  "summary": "2-4 sentence comparison explaining the score harshly and concretely"
}}
""".strip()
    resp = client.responses.create(
        model=model,
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    out = getattr(resp, "output_text", "") or "{}"
    try:
        raw = json.loads(out)
    except json.JSONDecodeError:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return _normalize_judge_payload(raw)


def make_report(
    run_id: str,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    one_shot_summary: dict[str, Any],
) -> str:
    lines = [
        f"# Retrieval Comparison: Oz CLI ({LIBRARY_ID}) vs Context7",
        "",
        f"- Corpus: Smallest AI Python SDK + Atoms + Waves",
        f"- Context7 ID: `{CTX7_ID}`",
        f"- Run ID: `{run_id}`",
        f"- Timestamp: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Queries: `{len(rows)}`",
        f"- Judge: strict one-shot coding-agent rubric",
        "",
        "## Aggregate",
        "",
        f"- Overall wins: oz={summary['overall_wins']['ours']}, context7={summary['overall_wins']['context7']}, tie={summary['overall_wins']['tie']}",
        f"- One-shot ready: oz={one_shot_summary['one_shot_ready']['ours']}, context7={one_shot_summary['one_shot_ready']['context7']}",
        f"- Avg output tokens est: oz={summary['avg_output_tokens_est']['ours']}, context7={summary['avg_output_tokens_est']['context7']}",
        f"- Avg latency ms: oz={summary['avg_timing_ms']['ours']}, context7={summary['avg_timing_ms']['context7']}",
        "",
        "| Metric | Oz | Context7 | Winner Count (oz/context7/tie) |",
        "| --- | ---: | ---: | --- |",
    ]
    for metric in base_eval.METRICS:
        wins = summary["wins_by_metric"][metric]
        lines.append(
            f"| {metric} | {summary['ours'][metric]} | {summary['context7'][metric]} | {wins['ours']}/{wins['context7']}/{wins['tie']} |"
        )

    lines.extend(["", "## Top Failure Tags", ""])
    for side, label in (("ours", "Oz"), ("context7", "Context7")):
        tags = one_shot_summary["top_failure_tags"][side]
        rendered = ", ".join(f"{item['tag']}={item['count']}" for item in tags) or "none"
        lines.append(f"- {label}: {rendered}")

    lines.extend(["", "## Per Query", ""])
    for idx, row in enumerate(rows, 1):
        judge = row["judge"]
        oz_tags = ", ".join(judge["ours"].get("failure_tags") or []) or "none"
        ctx_tags = ", ".join(judge["context7"].get("failure_tags") or []) or "none"
        lines.extend(
            [
                f"### {idx}. {row['query']}",
                f"- Overall winner: `{judge['overall_winner']}`",
                f"- Oz: latency={row['ours']['duration_ms']}ms, tokens≈{row['ours']['tokens_est']}, one-shot={judge['ours'].get('one_shot_ready')}, tags={oz_tags}",
                f"- Context7: latency={row['context7']['duration_ms']}ms, tokens≈{row['context7']['tokens_est']}, one-shot={judge['context7'].get('one_shot_ready')}, tags={ctx_tags}",
                f"- Judge summary: {judge['summary']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    base_eval.load_env(base_eval.ENV_PATH)
    base_eval.load_env(base_eval.EVAL_ENV_PATH, override=True)
    if base_eval.oz_eval_backend() == "api" and base_eval.EVAL_API_KEY_PATH.exists():
        fresh_eval_key = base_eval.EVAL_API_KEY_PATH.read_text(encoding="utf-8").strip()
        if fresh_eval_key:
            os.environ["OZ_API_KEY"] = fresh_eval_key

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY missing after loading .env")
    model = os.getenv("MODEL_BENCHMARK_JUDGE", "gpt-5.5")
    client = OpenAI(api_key=api_key)

    base_eval.OZ_LIBRARY_NAME_DEFAULT = OZ_LIBRARY_NAME_DEFAULT
    base_eval.OZ_VERSION_HINT_DEFAULT = OZ_VERSION_HINT_DEFAULT
    mcp_url, oz_api_key, library_name, version_hint, fallback_context_id = base_eval._oz_mcp_settings()

    base_eval.OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = base_eval.OUT_DIR / f"{run_id}_oz_smallest_ai_vs_context7.json"
    md_path = base_eval.OUT_DIR / f"{run_id}_oz_smallest_ai_vs_context7.md"
    partial_path = base_eval.OUT_DIR / f"{run_id}_oz_smallest_ai_vs_context7.partial.json"

    queries = QUERIES
    limit_raw = str(os.getenv("EVAL_QUERY_LIMIT") or "").strip()
    if limit_raw:
        try:
            queries = QUERIES[: max(1, int(limit_raw))]
        except ValueError:
            queries = QUERIES

    rows: list[dict[str, Any]] = []
    print(
        json.dumps(
            {
                "event": "benchmark_start",
                "runId": run_id,
                "queries": len(queries),
                "model": model,
                "mcpUrl": mcp_url,
                "libraryName": library_name,
                "versionHint": version_hint,
                "partial": str(partial_path),
            }
        ),
        flush=True,
    )
    for idx, query in enumerate(queries, 1):
        print(f"\n[{idx}/{len(queries)}] {query}", flush=True)
        ctx7_cmd = ["ctx7", "docs", CTX7_ID, query]
        ours_res = base_eval.retrieve_with_oz(
            query=query,
            mcp_url=mcp_url,
            api_key=oz_api_key,
            library_name=library_name,
            version_hint=version_hint,
            fallback_context_id=fallback_context_id,
            index=idx,
        )
        ctx7_res = base_eval.run_command(ctx7_cmd)
        ours_text = base_eval.clean_output(ours_res.stdout)
        ctx7_text = base_eval.clean_output(ctx7_res.stdout)
        if not ctx7_text and ctx7_res.stderr:
            ctx7_text = f"Context7 command failed: {ctx7_res.stderr}"
        if not ours_text and ours_res.stderr:
            ours_text = f"Oz CLI command failed: {ours_res.stderr}"
        print(
            f"  fetched: oz exit={ours_res.exit_code} latency={ours_res.duration_ms}ms tokens≈{base_eval.estimate_tokens(ours_text)} | "
            f"context7 exit={ctx7_res.exit_code} latency={ctx7_res.duration_ms}ms tokens≈{base_eval.estimate_tokens(ctx7_text)}",
            flush=True,
        )
        judge = judge_query(client, model, query, ours_text, ctx7_text)
        rows.append(
            {
                "index": idx,
                "query": query,
                "ours": {
                    "command": ours_res.command,
                    "duration_ms": ours_res.duration_ms,
                    "exit_code": ours_res.exit_code,
                    "stdout": ours_text,
                    "stderr": ours_res.stderr,
                    "tokens_est": base_eval.estimate_tokens(ours_text),
                },
                "context7": {
                    "command": ctx7_cmd,
                    "duration_ms": ctx7_res.duration_ms,
                    "exit_code": ctx7_res.exit_code,
                    "stdout": ctx7_text,
                    "stderr": ctx7_res.stderr,
                    "tokens_est": base_eval.estimate_tokens(ctx7_text),
                },
                "judge": judge,
            }
        )
        running = base_eval.aggregate(rows)
        one_shot_running = summarize_one_shot(rows)
        print(
            f"  scores: oz {_live_metric_line('ours', judge)} | context7 {_live_metric_line('context7', judge)}",
            flush=True,
        )
        print(f"  winner: {judge['overall_winner']} | {judge['summary']}", flush=True)
        print(f"  oz: {_live_tag_line('ours', judge)}", flush=True)
        print(f"  context7: {_live_tag_line('context7', judge)}", flush=True)
        print(
            "  running: "
            f"wins oz/context7/tie={running['overall_wins']['ours']}/{running['overall_wins']['context7']}/{running['overall_wins']['tie']} "
            f"avg_overall oz/context7={running['ours']['overall']}/{running['context7']['overall']} "
            f"one_shot oz/context7={one_shot_running['one_shot_ready']['ours']}/{one_shot_running['one_shot_ready']['context7']}",
            flush=True,
        )
        _write_partial_report(
            partial_path,
            run_id=run_id,
            rows=rows,
            queries=queries,
            model=model,
            mcp_url=mcp_url,
            library_name=library_name,
            version_hint=version_hint,
            fallback_context_id=fallback_context_id,
        )

    summary = base_eval.aggregate(rows)
    one_shot_summary = summarize_one_shot(rows)
    payload = {
        "libraryId": LIBRARY_ID,
        "context7Id": CTX7_ID,
        "oz": {
            "mcpUrl": mcp_url,
            "libraryName": library_name,
            "versionHint": version_hint,
            "fallbackContextId": fallback_context_id,
            "tools": ["oz pull", "oz context"],
        },
        "runId": run_id,
        "queries": queries,
        "metrics": base_eval.METRICS,
        "model": model,
        "rubric": "strict_one_shot_coding_agent",
        "summary": summary,
        "oneShotSummary": one_shot_summary,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(make_report(run_id, rows, summary, one_shot_summary), encoding="utf-8")
    try:
        partial_path.unlink()
    except FileNotFoundError:
        pass
    print(json.dumps({"json": str(json_path), "report": str(md_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
