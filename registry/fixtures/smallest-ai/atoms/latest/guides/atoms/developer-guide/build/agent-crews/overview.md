> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Agent Crews

> The brain of your AI application — the multi-node crew that handles conversation.

An **Agent Crew** is the core building block that powers conversational AI in the Atoms Agent Crews SDK. It's the "brain" that listens to what users say, thinks about how to respond, and speaks back — in real-time, with one or many cooperating nodes.

## What is an Agent Crew?

In Atoms, the simplest crew is a single `OutputCrewNode`—a specialized node that handles the complete conversation loop:

1. **Listen** — Receives transcribed speech from the user
2. **Think** — Processes the input with an LLM to generate a response
3. **Speak** — Streams the response as audio back to the user

This happens continuously, creating a natural back-and-forth conversation.

## Why Atoms Agent Crews?

| Feature                   | Description                                                            |
| ------------------------- | ---------------------------------------------------------------------- |
| **Real-Time Streaming**   | Responses start playing while the LLM is still generating. No waiting. |
| **Interruption Handling** | When users speak mid-response, the agent stops and listens.            |
| **Context Management**    | Conversation history maintained automatically.                         |
| **Tool Calling**          | Execute functions mid-conversation—check databases, call APIs.         |
| **Multi-Provider LLM**    | Use OpenAI, Anthropic, or bring your own model.                        |
| **Production Ready**      | Deploy with one command. Handle thousands of concurrent calls.         |

## Node Types

The SDK provides three node types for building agent crews:

| Node                 | Purpose                                               |
| -------------------- | ----------------------------------------------------- |
| `CrewNode`           | Base primitive for routing, logging, and custom logic |
| `OutputCrewNode`     | Conversational agent that speaks to users             |
| `BackgroundCrewNode` | Silent observer for analytics and monitoring          |

Deep dive into node architecture, when to use each type, and how to build custom nodes.

## What's Next

Set up prompts and LLM settings.

Give your agent actions and data access.

Conversation flows, interruptions, multi-agent.

Test locally and debug issues.
