> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Testing & Debugging

> Testing, debugging, and optimizing your agent.

**Testing and debugging** is how you ensure your agent works correctly before deploying to production. The SDK provides tools for local testing, logging, and diagnosing common issues.

## Why It Matters

Voice agents are harder to debug than web apps—you can't just refresh the page. Problems with latency, interruption handling, or tool execution only surface during real conversations.

The SDK gives you visibility into what's happening at every step.

## Key Capabilities

| Capability         | Description                                            |
| ------------------ | ------------------------------------------------------ |
| **Local Testing**  | Run agents on your machine with the CLI chat interface |
| **Logging**        | Trace events, LLM calls, and tool executions           |
| **Error Handling** | Graceful recovery from failures mid-conversation       |
| **Performance**    | Monitor latency and optimize response times            |

## What's Next

Trace execution flow and debug issues.

Troubleshooting FAQ and fixes.
