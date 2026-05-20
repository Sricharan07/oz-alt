# check_health

**Kind:** function
**Signature:** `import requests`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/endpoints/health-check

## Example

```python
import requests
import time

def check_health():
    try:
        response = requests.get(
            "http://localhost:7100/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

while True:
    if not check_health():
        print("Service unhealthy!")
    time.sleep(30)
```
