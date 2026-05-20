# Oz Agent Benchmark Harness

This directory contains a self-contained benchmark for measuring whether Oz helps coding agents find high-quality, low-token documentation context.

The first benchmark scope is intentionally small:

- `vercel/next.js`
- `facebook/react`
- `tiangolo/fastapi`
- 10 queries per library

The harness measures three layers:

1. Retrieval: Oz pull/search/context, expected-path hits, materialization, rough token budget.
2. Agent evidence: an optional `gpt-5.4-mini` Codex agent must use local Oz docs and write a grounded `benchmark_answer.json`.
3. Optional external-provider and multi-judge passes for apples-to-apples context comparison.

The judge is not automated by default. The harness writes `judge_packet.md` files with the task, Oz results, agent answer, oracle text when present, and evidence so a judge LLM or human can score consistently. Use `judge.py` when you intentionally want paid model judging.

## Quick Start

Validate cases and runner wiring:

```bash
python3 benchmark-harness/harness.py validate
```

Run deterministic Oz retrieval only:

```bash
python3 benchmark-harness/harness.py run --mode retrieval --limit 3
```

Run the expanded Next.js edge-case suite:

```bash
python3 benchmark-harness/harness.py run \
  --cases benchmark-harness/cases-nextjs-expanded.json \
  --mode retrieval \
  --library vercel/next.js
```

Run against the published npm-installed binary:

```bash
npm install --prefix /tmp/oz-bench-npm @hiringbae/oz@latest
python3 benchmark-harness/harness.py run \
  --mode retrieval \
  --oz-bin /tmp/oz-bench-npm/node_modules/.bin/oz \
  --skip-build
```

Run against production API data instead of the local checked-in registry:

```bash
python3 benchmark-harness/harness.py run \
  --mode retrieval \
  --oz-bin /tmp/oz-bench-npm/node_modules/.bin/oz \
  --skip-build \
  --api-url https://api.tryoz.dev \
  --app-url https://app.tryoz.dev \
  --create-prod-user
```

For non-interactive CI, provide an existing CLI token pair instead:

```bash
OZ_BENCH_AUTH_TOKEN=... OZ_BENCH_REFRESH_TOKEN=... \
python3 benchmark-harness/harness.py run \
  --mode retrieval \
  --api-url https://api.tryoz.dev
```

Run with release-quality gates enabled:

```bash
python3 benchmark-harness/harness.py run \
  --mode retrieval \
  --strict \
  --min-hit-at-5 0.8 \
  --min-required-terms 0.8 \
  --max-search-tokens 500
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

Compare the same case set against the Context7 context API:

```bash
CONTEXT7_API_KEY=... python3 benchmark-harness/context7_compare.py \
  --cases benchmark-harness/cases-nextjs-expanded.json \
  --library vercel/next.js \
  --context7-library-id /vercel/next.js \
  --oz-summary benchmark-harness/runs/<run-id>/summary.json \
  --out benchmark-harness/runs/<run-id>
```

Preferred provider-runner form:

```bash
CONTEXT7_API_KEY=... python3 benchmark-harness/provider_runner.py \
  --cases benchmark-harness/cases-nextjs-expanded.json \
  --provider context7 \
  --library vercel/next.js \
  --out benchmark-harness/runs/<run-id>/providers
```

Run optional multi-model judging over an existing Oz run:

```bash
OPENROUTER_API_KEY=... python3 benchmark-harness/judge.py \
  benchmark-harness/runs/<run-id> \
  --provider-summary benchmark-harness/runs/<run-id>/providers/context7_summary.json
```

Build a compact report:

```bash
python3 benchmark-harness/report.py \
  benchmark-harness/runs/<run-id> \
  --provider-summary benchmark-harness/runs/<run-id>/providers/context7_summary.json
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

Provider runs write under the directory passed to `--out`:

```txt
context7_raw_results.json
context7_case_scores.json
context7_summary.json
```

Automated judging writes:

```txt
judge_prompts/<case-id>.md
judge_results.json
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

By default the runner fails only when returned paths are not materialized locally. Use `--strict` for release gates over expected-path hit rate, required-term coverage, and compact search token budget. Those gates are meant to fail loudly when corpus quality regresses; do not loosen them to make a benchmark pass.

When `--api-url` is used, the harness writes CLI auth config only into temporary homes outside `benchmark-harness/runs` and deletes those homes after each case. Run artifacts intentionally never store access or refresh tokens.

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

## Provider And Judge Design

External provider comparisons are secondary. They normalize another context source into:

- output token estimate
- required-term coverage
- expected-source signal
- latency
- snippet/source count

That lets us compare snippet-heavy providers without changing the primary Oz path-first benchmark.

The optional multi-judge pass uses an OpenAI-compatible chat API, OpenRouter by default, and a majority vote across configured models. It should be used for release analysis, not for every local edit loop.
