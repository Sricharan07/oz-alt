> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Agent Crew CLI Reference

> Build, test, and deploy agent crews from the terminal.

The `smallestai agent-crew` CLI is built for rapid iteration. Test your crew locally with a single command, then deploy to the cloud when ready. No configuration files, no Docker, no infrastructure management.

**Local-first development**: Run and test your agent entirely on your machine. Deploy only when you're satisfied.

## Installation

The CLI comes bundled with the SDK:

```bash
pip install smallestai
```

Verify the installation:

```bash
smallestai --help
```

You'll also need an OpenAI API key for the example below — export it before running:

```bash
export OPENAI_API_KEY=sk-...
```

## Create Your First Agent Crew

Before the CLI has anything to connect to, you need a Python file that defines a crew and starts a WebSocket server. Pick one of the two patterns below and pull the example folder straight from the cookbook — the `tar` command drops a `getting_started/` or `background_agent/` directory into your cwd, ready to `cd` into. No `.env` file to set up; the examples read `OPENAI_API_KEY` straight from your shell. Each folder ships a one-line `requirements.txt` pinning `smallestai`, which the cloud build also uses when you `deploy`.

### Single-node crew

A minimal, single-node crew that streams chat completions from an LLM and greets the caller on join — copied from the cookbook's [`getting_started`](https://github.com/smallest-inc/cookbook/tree/main/voice-agents/getting_started).

```bash
curl -sL https://github.com/smallest-inc/cookbook/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 cookbook-main/voice-agents/getting_started
cd getting_started
```

`server.py` is the entry point — it boots an `AtomsCrewApp` on `ws://localhost:8080/ws`. `assistant.py` contains the `OutputCrewNode` subclass that streams the LLM response; extend it with your own prompt, tools, and logic.

### Multi-node crew with background processing

A two-node example from [`background_agent`](https://github.com/smallest-inc/cookbook/tree/main/voice-agents/background_agent) — a support agent talking to the user, and a sentiment analyzer running silently in parallel that flags frustration and triggers auto-escalation.

```bash
curl -sL https://github.com/smallest-inc/cookbook/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 cookbook-main/voice-agents/background_agent
cd background_agent
```

`app.py` wires both nodes into a single `CrewSession`. `support_agent.py` is the user-facing `OutputCrewNode`; it can query the sibling sentiment node mid-conversation. `sentiment_analyzer.py` is a `BackgroundCrewNode` — it listens to every transcript event, classifies sentiment, and updates state the support agent reads.

**What you're working with:**

* `OutputCrewNode` — base class for nodes that produce user-facing output. Override `generate_response()` to define what the agent says.
* `BackgroundCrewNode` — base class for nodes that observe events silently. Override `process_event()` to react. No audio output, no interrupts.
* `CrewSession` — the runtime that owns the WebSocket connection and runs your nodes in parallel for each call.
* `AtomsCrewApp` — the FastAPI WebSocket server that the CLI's `chat` command, and the production Atoms orchestrator, connect to.

## Local Development Workflow

The CLI's best feature is instant local testing. No need to deploy to test changes.

Run the entry point to start a local WebSocket server:

```bash
python server.py
```

This spins up a server on `localhost:8080` that mimics the production environment.

In another terminal, start an interactive voice session:

```bash
smallestai agent-crew chat
```

The CLI connects to your local server and lets you converse with your agent in real-time.

![CLI Chat](https://files.buildwithfern.com/smallest-ai.docs.buildwithfern.com/c1c0edfa424409aab0d12bba30d39913391d1405a21d7586ad47b4aadc3c7726/products/atoms/pages/images/cli-chat.png)

Make code changes, restart the server, and reconnect with `chat`. No redeploys needed.

## Cloud Deployment

When you're ready for production, deploy to Smallest AI's managed infrastructure.

**Prerequisite:** You must first create an agent on the [Atoms platform](https://atoms.smallest.ai) before deploying. The CLI links your local code to an existing platform agent.

```bash
smallestai auth login
```

Opens a browser for OAuth. Your credentials are stored locally.

```bash
smallestai agent-crew init
```

Select which agent from [atoms.smallest.ai](https://atoms.smallest.ai) to link your local code to.

```bash
smallestai agent-crew deploy --entry-point server.py
```

Packages your code and pushes it to the cloud. Takes about 30 seconds.

```bash
smallestai agent-crew builds
```

Select your build and choose **Make Live** to start serving traffic.

## Command Reference

### Authentication

| Command                  | Description                                |
| ------------------------ | ------------------------------------------ |
| `smallestai auth login`  | Authenticate with your Smallest AI account |
| `smallestai auth logout` | Clear stored credentials                   |

### Agent Management

| Command                        | Description                                |
| ------------------------------ | ------------------------------------------ |
| `smallestai agent-crew init`   | Link local directory to a platform agent   |
| `smallestai agent-crew deploy` | Deploy code to the cloud                   |
| `smallestai agent-crew builds` | View and manage deployments                |
| `smallestai agent-crew chat`   | Start interactive session with local agent |

### Common Options

| Option                 | Description                                         |
| ---------------------- | --------------------------------------------------- |
| `--entry-point ` | Specify the main Python file (default: `server.py`) |
| `--help`               | Show help for any command                           |

## Build Management

Deployments are not live by default. This gives you a safety buffer.

**One Live Build Per Agent**: Making a new build live automatically takes down the previous one.

**To promote a build:**

1. Run `smallestai agent-crew builds`
2. Select the desired build
3. Choose **Make Live**

**To roll back:**

1. Run `smallestai agent-crew builds`
2. Select the previous build
3. Choose **Make Live**

**To take down completely:**

1. Run `smallestai agent-crew builds`
2. Select the **LIVE** build
3. Choose **Take Down**

## More examples

The two crews above are the starting points. The [Smallest AI cookbook](https://github.com/smallest-inc/cookbook/tree/main/voice-agents) ships \~15 ready-to-run voice-agent examples covering tool calling, call control, multi-language support, knowledge-base grounding, real banking / scheduling / IVR flows, observability, and more — each in its own directory with the same `curl`-and-run shape.

Browse the full set of crews on GitHub.

STT, TTS, voice-agents, mobile, integrations — everything Smallest AI in one repo.
