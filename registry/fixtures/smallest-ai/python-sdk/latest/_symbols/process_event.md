# process_event

**Kind:** function
**Signature:** `class BackgroundAgentNode(Node):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/agent/nodes/background_agent.py#backgroundagentnode

## Example

```python
class BackgroundAgentNode(Node):
    """
    Base class for agents that do internal processing without output.

    This node type:
    - Does NOT automatically handle CONTROL_INTERRUPT
    - Does NOT emit output events automatically
    - Is designed for background processing like sentiment analysis, data extraction, etc.
    - Stores results internally or sends custom events

    Usage:
        class SentimentAnalyzer(BackgroundAgentNode):
            def __init__(self):
                super().__init__(name="sentiment")
                self.llm = OpenAIClient(model="gpt-4o-mini")
                self.results = {}

            async def process_event(self, event):
                if event.type == EventType.USER_TRANSCRIPTION:
                    sentiment = await self.analyze(event.text)
                    self.results[event.timestamp] = sentiment
                    # No output events - stores internally

            async def analyze(self, text: str):
                response = await self.llm.chat(
                    messages=[
                        {"role": "system", "content": "Analyze sentiment"},
                        {"role": "user", "content": text}
                    ]
                )
                return response.content
    """

    async def process_event(self, event: SDKEvent):
        """
        Process events (override in subclass).

        Note: This node type does NOT automatically handle interrupts.
        Override this method to handle events specific to your use case.

        Args:
            event: Event to process
        """
        pass
```
