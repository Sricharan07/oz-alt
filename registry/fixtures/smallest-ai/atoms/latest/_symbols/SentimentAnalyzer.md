# SentimentAnalyzer

**Kind:** class
**Signature:** `from smallestai.atoms.crew.nodes import BackgroundCrewNode`
**Source:** https://docs.smallest.ai/atoms/developer-guide/get-started/agent-crew-core-concepts/nodes

## Example

```python
from smallestai.atoms.crew.nodes import BackgroundCrewNode
from smallestai.atoms.crew.events import SDKEvent, SDKAgentTranscriptUpdateEvent

class SentimentAnalyzer(BackgroundCrewNode):
    def __init__(self):
        super().__init__(name="sentiment-analyzer")
        self.current_sentiment = "neutral"

    async def process_event(self, event: SDKEvent):
        if isinstance(event, SDKAgentTranscriptUpdateEvent):
            if event.role == "user":
                self.current_sentiment = await self._analyze(event.content)
```
