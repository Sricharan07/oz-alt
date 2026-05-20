# _get_remaining_fields

**Kind:** function
**Signature:** `class IntakeAgent(OutputCrewNode):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class IntakeAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="intake-agent")

        self.collected = {}
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover(self)
        self.tool_schemas = self.tool_registry.get_schemas()

    @function_tool()
    def record_information(
        self,
        field: str,
        value: str
    ) -> dict:
        """
        Record a piece of information from the conversation.

        Args:
            field: The type of information (name, email, phone, etc.)
            value: The value to record
        """
        self.collected[field] = value

        return {
            "recorded": f"{field}: {value}",
            "remaining": self._get_remaining_fields()
        }

    def _get_remaining_fields(self):
        required = ["name", "email", "reason"]
        return [f for f in required if f not in self.collected]
```
