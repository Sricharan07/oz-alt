# Oz Documentation Evidence Task

You are the coding/evidence agent for an Oz benchmark case.

You must use local Oz docs before answering. Do not use web search, model memory, or other documentation tools.

Required workflow:

1. Run `oz pull {library}` if docs are not already pulled.
2. Run `oz search "{query}" {library} --compact-json --max-results 10`.
3. Read the returned line windows first, not whole files. Use commands like
   `sed -n 'START,ENDp' <path>` from the `line`/`end_line` values.
4. Use `rg` inside `.codo/vendors/{library_prefix}` if the first windows are insufficient.
   Only read a whole file after the local line window and `rg` do not answer the task.
5. Write `benchmark_answer.json` in the current workspace.

The answer file must be valid JSON:

```json
{
  "case_id": "{case_id}",
  "library": "{library}",
  "query": "{query}",
  "selected_paths": [
    {
      "path": ".codo/vendors/...",
      "line": 1,
      "why": "short reason"
    }
  ],
  "answer": "source-grounded answer, concise but complete",
  "code_or_command_example": "code if the docs support one, otherwise empty string",
  "uncertainties": [],
  "tools_used": ["oz search", "line-window read", "rg"]
}
```

Rules:

- Prefer source-grounded correctness over breadth.
- Do not invent APIs not present in the local docs.
- Keep context small: line-window reads before full-file reads.
- Keep the answer useful for a coding agent.
- If Oz lacks enough docs, say that explicitly in `uncertainties`.
