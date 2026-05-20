> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Examples

> Full end-to-end code examples from the cookbook.

Complete, runnable examples you can deploy in minutes. Each example includes full source code, setup instructions, and deployment guide.

All examples are available in the [cookbook](https://github.com/smallest-inc/cookbook) repository.

## Getting Started

**5 min** · Build and deploy a basic conversational agent.

`OutputCrewNode` · `OpenAIClient` · `AtomsCrewApp` · CLI deployment

## Agent Development

**10 min** · Give your agent actions it can perform.

`@function_tool` · `ToolRegistry` · Tool execution · LLM function calling

**15 min** · Real-time sentiment analysis alongside your main agent.

`BackgroundCrewNode` · Multi-node architecture · Shared state · Silent processing

**10 min** · Configure how your agent handles user interruptions.

`is_interruptible` · Dynamic settings · Barge-in handling

**15 min** · Multilingual agent with language detection.

Language detection · Dynamic prompts · Multi-language support

## Calling

**10 min** · End calls and transfer to human agents.

`SDKAgentEndCallEvent` · `SDKAgentTransferConversationEvent` · Cold/warm transfers · Hold music

**15 min** · Build an interactive voice response menu.

Menu navigation · DTMF handling · Department routing

## Platform Features

**15 min** · Connect your agent to a knowledge base for accurate answers.

Knowledge base setup · RAG retrieval · Document upload

**20 min** · Run outbound calling campaigns at scale.

`AtomsClient` · Audience management · Campaign creation · Batch calling

## Analytics

**10 min** · Retrieve call metrics, transcripts, and post-call analysis.

Call details · Transcript export · Post-call configuration · Metrics API

## End-to-End Projects

**30 min** · Production-grade voice banking agent with real database queries, identity verification, and compliance logging.

`BackgroundCrewNode` · SQL execution · Multi-round tool chaining · KBA verification · Audit logging · Call transfers

**20 min** · Voice-based clinic receptionist that checks real Cal.com availability, negotiates time slots, and books appointments.

Cal.com API · Slot negotiation · `@function_tool` · Real calendar booking

**20 min** · State-machine-driven voice data collection with typed validation, backtracking, and native Jotform submission.

`FormEngine` · Step-by-step collection · Field validation · Jotform integration

## Observability & Integrations

**15 min** · Real-time voice agent observability with Langfuse via a BackgroundCrewNode — tool calls, LLM generations, and transcripts stream to your dashboard with zero latency impact.

`BackgroundCrewNode` · Langfuse traces · LLM generation tracking · Tool call spans

## Mobile Apps

**20 min** · Minimal React Native (Expo) app that opens a realtime voice session over the plain WebSocket endpoint. Mic capture, gapless PCM playback, mute toggle, in-app settings sheet that reconfigures voice, speed, and language via the REST draft-publish-activate flow. iOS and Android.

`wss://.../atoms/v1/agent/connect` · `react-native-audio-api` · `input_audio_buffer.append` · draft-publish-activate REST flow

## Running Examples

Each example follows the same pattern:

```bash
# Clone the cookbook
git clone https://github.com/smallest-inc/cookbook
cd cookbook/voice-agents/

# Install dependencies
pip install -e .

# Set environment variables
export OPENAI_API_KEY="your-key"

# Run locally
python app.py

# Test with CLI (in another terminal)
smallestai agent-crew chat
```

## Deploying Examples

```bash
# Login to Smallest AI
smallestai auth login

# Link to your agent
smallestai agent-crew init

# Deploy
smallestai agent-crew deploy --entry-point app.py

# Make live
smallestai agent-crew builds
```
