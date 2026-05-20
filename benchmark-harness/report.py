#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a compact markdown report for an Oz benchmark run.")
    parser.add_argument("run_dir")
    parser.add_argument("--provider-summary", action="append", default=[])
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"missing summary.json in {run_dir}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    provider_summaries = [load_json(Path(path)) for path in args.provider_summary if Path(path).exists()]
    judge = load_json(run_dir / "judge_results.json") if (run_dir / "judge_results.json").exists() else {}
    report = render_report(summary, provider_summaries, judge)
    out = Path(args.out) if args.out else run_dir / "report.md"
    out.write_text(report, encoding="utf-8")
    print(out)
    return 0


def render_report(summary: dict[str, Any], provider_summaries: list[dict[str, Any]], judge: dict[str, Any]) -> str:
    retrieval = summary.get("retrieval", {})
    lines = [
        "# Oz Benchmark Report",
        "",
        f"- Run: `{summary.get('run_id', '')}`",
        f"- Cases: {summary.get('case_count', 0)}",
        f"- Passed gates: {summary.get('passed')}",
        "",
        "## Oz Path-First Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "expected_path_hit_at_1",
        "expected_path_hit_at_5",
        "materialized_top5_rate",
        "required_terms_found_rate",
        "avg_search_tokens_est",
        "avg_context_tokens_est",
        "avg_docs_read_tokens_est",
    ):
        lines.append(f"| `{key}` | {retrieval.get(key, 0)} |")

    if provider_summaries:
        lines.extend(["", "## Provider Context Metrics", "", "| Provider | Ok | Expected source | Required terms | Tokens | Latency ms |", "|---|---:|---:|---:|---:|---:|"])
        for item in provider_summaries:
            provider_name = next((key for key in item.keys() if key not in {"results", "case_count", "provider_config"}), "")
            data = item.get(provider_name, {}) if provider_name else {}
            lines.append(
                "| "
                f"{provider_name} | "
                f"{data.get('ok_rate', 0)} | "
                f"{data.get('expected_source_signal_rate', 0)} | "
                f"{data.get('required_terms_found_rate', 0)} | "
                f"{data.get('avg_context_tokens_est', 0)} | "
                f"{data.get('avg_latency_ms', 0)} |"
            )

    judge_summary = judge.get("summary", {}) if isinstance(judge, dict) else {}
    if judge_summary:
        lines.extend(
            [
                "",
                "## Multi-Judge Summary",
                "",
                f"- Judged cases: {judge_summary.get('judged_count', 0)}",
                f"- Pass rate: {judge_summary.get('pass_rate', 0)}",
                f"- Average score: {judge_summary.get('avg_overall_score', 0)}",
            ]
        )

    lines.extend(["", "## Gates", "", "```json", json.dumps(summary.get("gates", {}), indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
