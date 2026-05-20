# MyAgent

**Kind:** class
**Signature:** `class MyAgent(OutputCrewNode):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class MyAgent(OutputCrewNode):
    async def generate_response(self):
        # Access full message history
        all_messages = self.context.messages

        # Get the last user message
        user_messages = [m for m in all_messages if m["role"] == "user"]
        last_user = user_messages[-1]["content"] if user_messages else ""

        # Count turns
        user_turns = sum(1 for m in all_messages if m["role"] == "user")
```
