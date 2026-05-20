> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Analytics

> Track every call, measure performance, and extract insights.

**Analytics** gives you complete visibility into what happens during and after every call your agents handle.

## What Can You Track?

Every call generates rich data that you can access programmatically:

| Category                | Data Available                              |
| ----------------------- | ------------------------------------------- |
| **Call Details**        | Duration, status, phone numbers, timestamps |
| **Transcript**          | Full conversation text with speaker labels  |
| **Recordings**          | Mono and stereo audio files                 |
| **AI Summaries**        | Auto-generated call summaries               |
| **Disposition Metrics** | Extracted data points you define            |
| **Performance**         | Latency breakdowns per component            |
| **Cost**                | Credits consumed per call                   |

## How It Works

1. **During the call** — Events are logged in real-time (status changes, transcription, speech)
2. **After the call** — AI processes the transcript to generate summaries and extract configured metrics
3. **On demand** — SDK methods let you query, filter, and search call data

## SDK Methods

| Method                                | Purpose                        |
| ------------------------------------- | ------------------------------ |
| `get_calls()`                         | List calls with filters        |
| `get_call(id)`                        | Get single call details        |
| `search_calls(ids)`                   | Batch fetch by call IDs        |
| `get_post_call_config(agent_id)`      | Get agent's analytics config   |
| `set_post_call_config(agent_id, ...)` | Configure post-call extraction |

## What's Next

Retrieve calls, transcripts, recordings, and performance data.

Configure AI summaries and disposition metrics.
