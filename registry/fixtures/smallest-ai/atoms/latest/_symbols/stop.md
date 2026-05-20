# stop

**Kind:** function
**Signature:** `import redis`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/agent-crews/patterns/state-management

## Example

```python
import redis

class PersistentAgent(OutputCrewNode):
    def __init__(self):
        super().__init__(name="persistent-agent")
        self.redis = redis.Redis()

    async def start(self, init_event, task_manager):
        await super().start(init_event, task_manager)

        phone = init_event.session_context.initial_variables.get("phone")

        # Load previous state
        stored = self.redis.get(f"user:{phone}")
        if stored:
            self.user_data = json.loads(stored)
        else:
            self.user_data = {}

    async def stop(self):
        # Save state before session ends
        phone = self.init_event.session_context.initial_variables.get("phone")
        self.redis.set(f"user:{phone}", json.dumps(self.user_data))
        await super().stop()
```
