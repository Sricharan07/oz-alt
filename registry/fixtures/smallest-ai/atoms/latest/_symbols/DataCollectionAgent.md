# DataCollectionAgent

**Kind:** class
**Signature:** `class DataCollectionAgent(OutputCrewNode):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
class DataCollectionAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="data-agent")

        # Session state
        self.customer_name = None
        self.email = None
        self.phone = None
        self.order_id = None

    @function_tool()
    def save_customer_info(
        self,
        name: str = None,
        email: str = None,
        phone: str = None
    ) -> dict:
        """Save customer information."""
        if name:
            self.customer_name = name
        if email:
            self.email = email
        if phone:
            self.phone = phone

        return {"saved": True, "collected": self._get_collected()}

    def _get_collected(self) -> dict:
        return {
            "name": self.customer_name,
            "email": self.email,
            "phone": self.phone
        }
```
