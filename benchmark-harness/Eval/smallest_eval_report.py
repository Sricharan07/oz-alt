from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import eval as base_eval


def make_report(
    run_id: str,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    one_shot_summary: dict[str, Any],
    *,
    library_id: str,
    ctx7_id: str,
) -> str:
    lines = [
        f"# Retrieval Comparison: Oz CLI ({library_id}) vs Context7",
        "",
        "- Corpus: Smallest AI Python SDK + Atoms + Waves",
        f"- Context7 ID: `{ctx7_id}`",
        f"- Run ID: `{run_id}`",
        f"- Timestamp: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Queries: `{len(rows)}`",
        "- Judge: strict one-shot coding-agent rubric",
        "",
        "## Aggregate",
        "",
        f"- Overall wins: oz={summary['overall_wins']['ours']}, context7={summary['overall_wins']['context7']}, tie={summary['overall_wins']['tie']}",
        f"- One-shot ready: oz={one_shot_summary['one_shot_ready']['ours']}, context7={one_shot_summary['one_shot_ready']['context7']}",
        f"- Avg output tokens est: oz={summary['avg_output_tokens_est']['ours']}, context7={summary['avg_output_tokens_est']['context7']}",
        f"- Avg latency ms: oz={summary['avg_timing_ms']['ours']}, context7={summary['avg_timing_ms']['context7']}",
        f"- Judge runs per query: {rows[0]['judge'].get('judge_count', 0) if rows else 0}",
        "",
        "| Metric | Oz | Context7 | Winner Count (oz/context7/tie) |",
        "| --- | ---: | ---: | --- |",
    ]
    for metric in base_eval.METRICS:
        wins = summary["wins_by_metric"][metric]
        lines.append(
            f"| {metric} | {summary['ours'][metric]} | {summary['context7'][metric]} | {wins['ours']}/{wins['context7']}/{wins['tie']} |"
        )

    deterministic = summary.get("deterministic", {})
    if deterministic:
        lines.extend(
            [
                "",
                "## Deterministic Criteria",
                "",
                "| Metric | Oz | Context7 |",
                "| --- | ---: | ---: |",
            ]
        )
        for metric in (
            "expected_api_recall",
            "required_terms_found_rate",
            "expected_path_recall",
            "precision_proxy",
            "deterministic_pass_rate",
            "latency_p50_ms",
            "latency_p95_ms",
        ):
            lines.append(
                f"| {metric} | {deterministic.get('ours', {}).get(metric, 0)} | {deterministic.get('context7', {}).get(metric, 0)} |"
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
                f"- Category: `{row.get('case', {}).get('category', '')}`",
                f"- Overall winner: `{judge['overall_winner']}`",
                f"- Oz: latency={row['ours']['duration_ms']}ms, tokens≈{row['ours']['tokens_est']}, one-shot={judge['ours'].get('one_shot_ready')}, tags={oz_tags}",
                f"- Context7: latency={row['context7']['duration_ms']}ms, tokens≈{row['context7']['tokens_est']}, one-shot={judge['context7'].get('one_shot_ready')}, tags={ctx_tags}",
                f"- Deterministic: oz_api_recall={row.get('deterministic', {}).get('ours', {}).get('expected_api_recall')} context7_api_recall={row.get('deterministic', {}).get('context7', {}).get('expected_api_recall')}",
                f"- Judge summary: {judge['summary']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
