# Provider Configs

Provider runs are secondary comparisons against context-returning tools. They do not replace the Oz path-first benchmark.

Supported kinds:

- `context7_api`: calls the Context7 HTTP context endpoint and normalizes code/info snippets.
- `command`: runs a local command with `{query}`, `{library}`, and `{max_tokens}` substitutions, then normalizes JSON `results[]` or plain stdout.

Example command provider:

```json
{
  "name": "my-provider",
  "kind": "command",
  "command": ["my-doc-tool", "context", "{query}", "{library}", "--max-tokens", "{max_tokens}"]
}
```

Provider outputs are scored on token estimate, required-term coverage, expected-source signal, latency, and snippet/source count.
