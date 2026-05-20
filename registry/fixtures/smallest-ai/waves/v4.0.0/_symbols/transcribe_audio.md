# transcribe_audio

**Kind:** function
**Signature:** `import requests`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```python
import requests
import os

LICENSE_KEY = os.getenv("LICENSE_KEY")
API_URL = "http://localhost:7100"

def transcribe_audio(audio_url):
    response = requests.post(
        f"{API_URL}/v1/listen",
        headers={
            "Authorization": f"Token {LICENSE_KEY}",
            "Content-Type": "application/json"
        },
        json={"url": audio_url}
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Transcription failed: {response.text}")

result = transcribe_audio("https://example.com/audio.wav")
print(f"Transcription: {result['text']}")
print(f"Confidence: {result['confidence']}")
```
