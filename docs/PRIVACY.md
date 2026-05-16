# Oz Privacy Policy

Last updated: May 16, 2026

Oz collects the minimum operational data needed to run the public beta.

## What Oz Collects

- CLI command event name.
- Anonymous user identifier.
- Library names involved in pull, update, suggest, and search flows.
- Query length and result count for suggest/search.
- Error class and status code for failed registry operations.
- Agent install target names selected by the user.

## What Oz Does Not Collect

- Source code.
- File contents.
- Full file paths from user projects.
- Suggest or search query text.
- Documentation content read by the agent.
- Secrets, environment variables, or lockfile contents.

## Telemetry Controls

Telemetry is disclosed during `oz login` and is on by default for the beta. Disable it with:

```bash
oz config set telemetry off
```

## Credential Storage

The CLI stores auth tokens in the OS keychain when available:

- macOS Keychain
- Windows Credential Manager
- Linux Secret Service via `secret-tool`

If keychain access fails, Oz falls back to `~/.codo/config.json`.

## Data Retention

- Telemetry events: 90 days.
- Index requests: retained until resolved, then archived.
- Rerank cache: 7 days.
- Authentication logs: 30 days.

## Contact

Security and privacy issues should be reported to the project owner before public disclosure.
