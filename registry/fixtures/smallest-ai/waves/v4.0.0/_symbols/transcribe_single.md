# transcribe_single

**Kind:** function
**Signature:** `import concurrent.futures`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```python
import concurrent.futures
import requests
import os

LICENSE_KEY = os.getenv("LICENSE_KEY")
API_URL = "http://localhost:7100"

def transcribe_single(audio_url):
    try:
        response = requests.post(
            f"{API_URL}/v1/listen",
            headers={
                "Authorization": f"Token {LICENSE_KEY}",
                "Content-Type": "application/json"
            },
            json={"url": audio_url},
            timeout=300
        )
        response.raise_for_status()
        return {
            "url": audio_url,
            "success": True,
            "result": response.json()
        }
    except Exception as e:
        return {
            "url": audio_url,
            "success": False,
            "error": str(e)
        }

audio_urls = [
    "https://example.com/audio1.wav",
    "https://example.com/audio2.wav",
    "https://example.com/audio3.wav",
]

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(transcribe_single, audio_urls))

for result in results:
    if result['success']:
        print(f"{result['url']}: {result['result']['text']}")
    else:
        print(f"{result['url']}: ERROR - {result['error']}")
```
