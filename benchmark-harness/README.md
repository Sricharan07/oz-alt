# Oz Agent Benchmark Harness

This directory contains a self-contained benchmark for measuring whether Oz helps coding agents find high-quality, low-token documentation context.

The first benchmark scope is intentionally small:

- `vercel/next.js`
- `facebook/react`
- `tiangolo/fastapi`
- 10 queries per library

The harness measures two layers:

1. Retrieval: Oz pull/search/context, expected-path hits, materialization, rough token budget.
2. Agent evidence: an optional `gpt-5.4-mini` Codex agent must use local Oz docs and write a grounded `benchmark_answer.json`.

The judge is not automated by default. The harness writes `judge_packet.md` files with the task, Oz results, agent answer, and evidence so a judge LLM or human can score consistently.

## Quick Start

Validate cases and runner wiring:

```bash
python3 benchmark-harness/harness.py validate
```

Run deterministic Oz retrieval only:

```bash
python3 benchmark-harness/harness.py run --mode retrieval --limit 3
```

Run the mini coding/evidence agent on one case:

```bash
python3 benchmark-harness/harness.py run \
  --mode agent \
  --case nextjs-middleware-auth-cookies \
  --agent-model gpt-5.4-mini
```

Summarize a run:

```bash
python3 benchmark-harness/harness.py summarize benchmark-harness/runs/<run-id>
```

## Modes

`retrieval` runs only Oz commands:

- `oz init`
- `oz pull <library>`
- `oz search "<query>" <library> --compact-json`
- `oz context "<query>" <library> --json`
- local line-window reads from `.codo/vendors`

`agent` does the retrieval pass, then runs:

```bash
codex exec --model gpt-5.4-mini ...
```

The agent prompt requires the agent to use Oz/local `.codo` docs and produce `benchmark_answer.json`.

## Outputs

Every run writes under `benchmark-harness/runs/<timestamp>/`:

```txt
summary.json
cases/<case-id>/
  case.json
  workspace/
  oz_search.json
  oz_context.json
  read_files.json
  retrieval_metrics.json
  agent_prompt.md
  agent_stdout.jsonl
  agent_stderr.log
  benchmark_answer.json
  judge_packet.md
```

## What This Measures

Primary metrics:

- `expected_path_hit_at_1`
- `expected_path_hit_at_5`
- `materialized_top5_rate`
- `required_terms_found_rate`
- `oz_search_output_tokens_est`
- `oz_context_output_tokens_est`
- `docs_read_tokens_est` for bounded line windows, not full files
- `agent_answer_exists`

This is deliberately filesystem-based. Oz's advantage is path-first retrieval plus native file reads, so a pure snippet API eval would under-measure the product.

The retrieval runner reads only the top bounded line window by default. This matches the intended agent workflow: use Oz to find a precise location, inspect that local window, then expand with `rg`, more result windows, or full-file reads only when needed. Use `--read-results N` to intentionally model a broader read strategy.

## Judging Rubric

Score each `judge_packet.md` from 0 to 5:

- 5: Correct, source-grounded, version-aware, minimal context, useful code/API guidance.
- 4: Correct and grounded, with minor missing nuance.
- 3: Mostly correct, but incomplete or too much irrelevant context.
- 2: Partially relevant, risky, or weakly sourced.
- 1: Mostly wrong or noisy.
- 0: No useful answer or no docs evidence.

Track separately:

- hallucinated API: yes/no
- expected source used: yes/no
- excessive context: yes/no
- version mismatch: yes/no
