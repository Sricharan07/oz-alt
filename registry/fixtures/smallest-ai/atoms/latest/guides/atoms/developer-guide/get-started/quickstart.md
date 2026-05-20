> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Quick Start

> Install the SDK, build an agent crew, and run it.

Install the SDK, write your first agent crew, and test it — locally or deployed to the cloud.

## Prerequisites

**OpenAI API Key required.** Set it as an environment variable before running your agent:

```bash
export OPENAI_API_KEY="your-key-here"
```

## Installation

```bash
pip install smallestai
```

## Write Your First Agent Crew

Create two files: one for the crew node logic, and one to run the server.

Subclass `OutputCrewNode` and implement `generate_response()` to stream LLM output.

```python assistant.py
import os
from smallestai.atoms.crew.nodes import OutputCrewNode
from smallestai.atoms.crew.clients.openai import OpenAIClient

class Assistant(OutputCrewNode):
    def __init__(self):
        super().__init__(name="assistant")
        self.llm = OpenAIClient(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def generate_response(self):
        response = await self.llm.chat(
            messages=self.context.messages,
            stream=True
        )
        async for chunk in response:
            if chunk.content:
                yield chunk.content
```

Wire up `AtomsCrewApp` with a `setup_handler` that adds your crew node to the session.

```python server.py
from smallestai.atoms.crew.server import AtomsCrewApp
from smallestai.atoms.crew.session import CrewSession
from assistant import Assistant

async def on_start(session: CrewSession):
    session.add_node(Assistant())
    await session.start()
    await session.wait_until_complete()

if __name__ == "__main__":
    app = AtomsCrewApp(setup_handler=on_start)
    app.run()
```

Your entry point can be named anything (`run.py`, `serve.py`, etc.). When deploying, specify it with `--entry-point your_server.py`.

**Want a greeting?** Use `@session.on_event` to speak when the user joins:

```python
@session.on_event("on_event_received")
async def on_event(_, event):
    if isinstance(event, SDKSystemUserJoinedEvent):
        agent.context.add_message({"role": "assistant", "content": "Hello!"})
        await agent.speak("Hello! How can I help?")
```

Adding the greeting to context ensures the LLM knows the conversation has started.

## Run Your Agent Crew

Once your files are ready, you have two options:

For development and testing, run the file directly:

```bash
python server.py
```

This starts a WebSocket server on `localhost:8080`. In a separate terminal, connect to it:

```bash
smallestai agent-crew chat
```

No account or deployment needed.

To have Smallest AI host your agent in the cloud (for production, API access, or phone calls):

**Prerequisite:** You must first create an agent on the [Atoms platform](https://app.smallest.ai?utm_source=documentation\&utm_medium=docs). The `agent init` command links your local code to that agent.

```bash
smallestai auth login
```

Link your directory to an existing agent on the platform.

```bash
smallestai agent-crew init
```

Push your code to the cloud.

```bash
smallestai agent-crew deploy --entry-point server.py
```

Run `smallestai agent-crew builds`, select your build, and choose **Make Live**.

## What's Next?

Give your agent calculators, search, and APIs.

Connect multiple agents for complex workflows.

\~15 ready-to-run voice-agent crews — tool calling, IVR, multi-language, background processing, and more.

Full CLI reference — local testing, deploy, builds management.

### Need Help?

Ask questions, share what you're building, and get help from other developers.
