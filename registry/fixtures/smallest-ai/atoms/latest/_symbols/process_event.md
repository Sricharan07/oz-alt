# process_event

**Kind:** function
**Signature:** `class RouterNode(Node):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class RouterNode(Node):
    async def process_event(self, event):
        # Store routing decision in event metadata
        event.metadata["routed_to"] = "sales"
        await self.send_event(event)

class SalesAgent(OutputCrewNode):
    async def process_event(self, event):
        # Read state from event
        if event.metadata.get("routed_to") == "sales":
            await super().process_event(event)
```
