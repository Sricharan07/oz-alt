> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Agent Crew Core Concepts

> The fundamental building blocks of the Atoms Agent Crews SDK — nodes, sessions, events, and graphs.

The Atoms Agent Crews SDK is built around a **graph-based architecture** where information flows between processing units. This design makes it easy to build everything from simple single-node swarms to complex multi-node orchestration.

## How It Works

Every voice conversation in Atoms follows this pattern:

1. **Audio comes in** — The user speaks into their phone or browser
2. **Events flow through nodes** — Speech is transcribed, processed, and responses generated
3. **Audio goes out** — The agent's response is synthesized and played back

The system manages all the complexity of real-time streaming, interruptions, and state management. You just focus on the logic.

## The Four Building Blocks

Processing units that handle events. The brain of your agent logic.

Messages flowing through the system. Audio, text, and control signals.

Connect nodes into pipelines. Build complex multi-agent flows.

Manage conversation state and lifecycle. One session per call.
