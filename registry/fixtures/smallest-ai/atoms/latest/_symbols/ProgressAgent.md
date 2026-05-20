# ProgressAgent

**Kind:** class
**Signature:** `class ProgressAgent(OutputCrewNode):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class ProgressAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="progress-agent")
        self.turn_count = 0
        self.started_at = None

    async def start(self, init_event, task_manager):
        await super().start(init_event, task_manager)
        self.started_at = datetime.now()

    async def generate_response(self):
        self.turn_count += 1

        # Different behavior based on turn count
        if self.turn_count == 1:
            yield "Welcome! This is our first exchange."
        elif self.turn_count > 10:
            yield "We've been chatting for a while. "
            yield "Is there anything else I can help with?"
```
