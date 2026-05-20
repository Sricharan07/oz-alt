# call_api

**Kind:** function
**Signature:** `from ratelimit import limits, sleep_and_retry`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/authentication

## Example

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)
def call_api():
    response = requests.post(...)
    return response
```
