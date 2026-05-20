#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

import eval as base_eval


LIBRARY_ID = os.getenv("OZ_EVAL_LIBRARY_ID", "/smallest/py-sdk")
CTX7_ID = os.getenv("CTX7_ID", "/smallest-inc/smallest-python-sdk")
OZ_LIBRARY_NAME_DEFAULT = os.getenv("OZ_EVAL_LIBRARY_NAME_DEFAULT", "Smallest AI")
OZ_VERSION_HINT_DEFAULT = os.getenv("OZ_EVAL_VERSION_HINT_DEFAULT", "latest")

QUERIES = [
    "How do I install and initialize the Smallest AI Python SDK?",
    "How do I authenticate with a Smallest API key in Python?",
    "How do I synthesize speech with Waves using the Python SDK?",
    "How do I stream text to speech audio with Waves in Python?",
    "How do I use Atoms to build or run a voice agent?",
    "What are the required parameters for a Waves text to speech request?",
    "How do I choose or configure a voice/model for Smallest text to speech?",
    "How do I save generated audio to a file in Python?",
    "How do I handle errors from Smallest API calls in the Python SDK?",
    "Show a complete minimal Python example that sends text to Smallest and plays or writes the audio output.",
]


def judge_query(client: OpenAI, model: str, query: str, ours: str, context7: str) -> dict[str, Any]:
    prompt = f"""
You are a strict evaluator for documentation retrieval used by a coding agent.

The coding agent needs source-grounded context that helps it write correct code immediately.
Be harsh. Do not reward generic summaries, marketing prose, empty packet headings, or text that lacks concrete API usage.

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

Hard caps:
- If an output is an error, empty, or says evidence is unavailable, overall must be <= 2.
- If it has no concrete API/method/parameter information for a how-to query, overall must be <= 5.
- If it is relevant but missing code for a code-shaped query, code_utility must be <= 5.
- If it appears ungrounded or cannot be traced to source docs, source_grounding must be <= 5.
- If it retrieves the wrong product area, overall must be <= 3.

Return strict JSON with this shape:
{{
  "ours": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0}},
  "context7": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0}},
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
    return json.loads(out)


def make_report(run_id: str, rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        f"# Retrieval Comparison: Oz CLI ({LIBRARY_ID}) vs Context7",
        "",
        f"- Corpus: Smallest AI Python SDK + Atoms + Waves",
        f"- Context7 ID: `{CTX7_ID}`",
        f"- Run ID: `{run_id}`",
        f"- Timestamp: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Queries: `{len(rows)}`",
        f"- Judge: strict coding-agent rubric",
        "",
        "## Aggregate",
        "",
        f"- Overall wins: oz={summary['overall_wins']['ours']}, context7={summary['overall_wins']['context7']}, tie={summary['overall_wins']['tie']}",
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

    lines.extend(["", "## Per Query", ""])
    for idx, row in enumerate(rows, 1):
        judge = row["judge"]
        lines.extend(
            [
                f"### {idx}. {row['query']}",
                f"- Overall winner: `{judge['overall_winner']}`",
                f"- Oz: latency={row['ours']['duration_ms']}ms, tokens≈{row['ours']['tokens_est']}",
                f"- Context7: latency={row['context7']['duration_ms']}ms, tokens≈{row['context7']['tokens_est']}",
                f"- Judge summary: {judge['summary']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    base_eval.load_env(base_eval.ENV_PATH)
    base_eval.load_env(base_eval.EVAL_ENV_PATH, override=True)
    if base_eval.EVAL_API_KEY_PATH.exists():
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

    queries = QUERIES
    limit_raw = str(os.getenv("EVAL_QUERY_LIMIT") or "").strip()
    if limit_raw:
        try:
            queries = QUERIES[: max(1, int(limit_raw))]
        except ValueError:
            queries = QUERIES

    rows: list[dict[str, Any]] = []
    for idx, query in enumerate(queries, 1):
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

    summary = base_eval.aggregate(rows)
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
        "rubric": "strict_coding_agent",
        "summary": summary,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(make_report(run_id, rows, summary), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "report": str(md_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
