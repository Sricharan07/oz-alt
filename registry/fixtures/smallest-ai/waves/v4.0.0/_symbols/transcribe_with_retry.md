# transcribe_with_retry

**Kind:** function
**Signature:** `from tenacity import retry, stop_after_attempt, wait_exponential`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def transcribe_with_retry(audio_url):
    return client.transcribe(audio_url)
```
