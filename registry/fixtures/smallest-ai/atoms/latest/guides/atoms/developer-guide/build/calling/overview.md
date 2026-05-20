> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Calling

> Make outbound calls with your AI agent.

The Atoms Agent Crews SDK lets you make outbound phone calls. Connect your AI agents to real phone conversations.

## What Can You Do?

| Capability         | Description                                            |
| ------------------ | ------------------------------------------------------ |
| **Outbound Calls** | Dial any phone number and connect it to your agent     |
| **Call Control**   | End calls or transfer to humans from within your agent |
| **Call Logs**      | Access transcripts, recordings, and analytics          |

## How It Works

```
Your App → SDK → Atoms Platform → Phone Network → User's Phone
                      ↓
                 Your Agent
```

1. **You initiate** — Call `start_outbound_call()` with a phone number
2. **Platform connects** — Atoms dials the number and establishes the call
3. **Agent handles** — Your agent runs the conversation in real-time
4. **You analyze** — Access transcripts and analytics afterward

## Prerequisites

Before making calls:

1. **API Key** — Get from [atoms.smallest.ai](https://atoms.smallest.ai)
2. **Agent** — Create an agent in the dashboard with a phone number linked
3. **Phone Numbers** — E.164 format (e.g., `+14155551234`)

## What's Next

Make individual calls with code examples.

End calls and transfer to humans.
