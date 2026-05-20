# __init__

**Kind:** function
**Signature:** `import requests`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

class SmallestClient:
    def __init__(self, api_url, license_key):
        self.api_url = api_url
        self.license_key = license_key

        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def transcribe(self, audio_url, **kwargs):
        headers = {
            "Authorization": f"Token {self.license_key}",
            "Content-Type": "application/json"
        }

        payload = {"url": audio_url, **kwargs}

        response = self.session.post(
            f"{self.api_url}/v1/listen",
            headers=headers,
            json=payload,
            timeout=300
        )

        response.raise_for_status()
        return response.json()

client = SmallestClient(
    api_url="http://localhost:7100",
    license_key=os.getenv("LICENSE_KEY")
)

result = client.transcribe(
    "https://example.com/audio.wav",
    punctuate=True,
    timestamps=True
)
print(result['text'])
```
