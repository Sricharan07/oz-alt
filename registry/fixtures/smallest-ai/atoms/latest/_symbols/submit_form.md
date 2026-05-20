# submit_form

**Kind:** function
**Signature:** `class ValidationAgent(OutputCrewNode):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class ValidationAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="validation-agent")
        self.data = {}

    @function_tool()
    def submit_form(self) -> dict:
        """Submit the collected information."""
        errors = []

        if not self.data.get("name"):
            errors.append("Name is required")

        if not self.data.get("email"):
            errors.append("Email is required")
        elif "@" not in self.data["email"]:
            errors.append("Email format is invalid")

        if errors:
            return {"success": False, "errors": errors}

        return {"success": True, "data": self.data}
```
