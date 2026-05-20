# start

**Kind:** function
**Signature:** `async def start(self, init_event, task_manager):`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
async def start(self, init_event, task_manager):
    await super().start(init_event, task_manager)

    ctx = init_event.session_context

    # Access initial variables
    self.customer_id = ctx.initial_variables.get("customer_id")
    self.account_tier = ctx.initial_variables.get("tier")
    self.language = ctx.initial_variables.get("language", "en")

    # Use them to customize behavior
    if self.account_tier == "premium":
        self.context.add_message({
            "role": "system",
            "content": "This is a premium customer. Prioritize their requests."
        })
```
