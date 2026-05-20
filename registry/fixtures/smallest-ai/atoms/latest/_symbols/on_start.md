# on_start

**Kind:** function
**Signature:** `import os`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/llm/byom

## Example

```python
import os
from smallestai.atoms.crew.nodes import OutputCrewNode
from smallestai.atoms.crew.clients.openai import OpenAIClient
from smallestai.atoms.crew.server import AtomsCrewApp
from smallestai.atoms.crew.session import CrewSession

class LocalAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="local-agent")

        # Connect to your local model
        self.llm = OpenAIClient(
            model="llama3",
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Not required for Ollama
        )

        self.context.add_message(
            "system",
            "You are a helpful assistant running on local hardware."
        )

    async def generate_response(self):
        response = await self.llm.chat(
            messages=self.context.messages,
            stream=True
        )
        async for chunk in response:
            if chunk.content:
                yield chunk.content

async def on_start(session: CrewSession):
    session.add_node(LocalAgent())
    await session.start()
    await session.wait_until_complete()

if __name__ == "__main__":
    app = AtomsCrewApp(setup_handler=on_start)
    app.run()
```
