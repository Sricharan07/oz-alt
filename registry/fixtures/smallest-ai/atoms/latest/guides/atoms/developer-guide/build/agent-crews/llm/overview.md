> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Configuration

> Setting up the brain of your agent.

**Configuration** is how you define your agent's behavior—which LLM it uses and how it responds. Get this right and your agent feels natural. Get it wrong and users will notice.

## What is Configuration?

Every agent needs two things configured:

1. **LLM Settings** — Which model to use, temperature, streaming behavior
2. **Prompts** — System instructions that define personality and constraints

The SDK provides sensible defaults, so you can start simple and tune later.

## Key Settings

| Setting           | What It Controls                                             |
| ----------------- | ------------------------------------------------------------ |
| **Model**         | GPT-4o, Claude, Llama, or your own                           |
| **Temperature**   | 0.0 = deterministic, 1.0 = creative                          |
| **Streaming**     | Essential for real-time responses (always use `stream=True`) |
| **System Prompt** | The personality, rules, and context                          |

## What's Next

Craft effective system prompts that define behavior.

Model selection, temperature, and streaming.

Run local models with Ollama, vLLM, or custom servers.
