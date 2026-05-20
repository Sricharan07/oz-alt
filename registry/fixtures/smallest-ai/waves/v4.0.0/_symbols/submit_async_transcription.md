# submit_async_transcription

**Kind:** function
**Signature:** `from flask import Flask, request, jsonify`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```python
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

LICENSE_KEY = os.getenv("LICENSE_KEY")
API_URL = "http://localhost:7100"

@app.route('/webhook/transcription', methods=['POST'])
def transcription_webhook():
    data = request.json
    job_id = data['job_id']
    status = data['status']

    if status == 'completed':
        result = data['result']
        print(f"Job {job_id} completed: {result['text']}")
    elif status == 'failed':
        print(f"Job {job_id} failed: {data['error']}")

    return jsonify({"received": True})

def submit_async_transcription(audio_url):
    response = requests.post(
        f"{API_URL}/v1/listen",
        headers={
            "Authorization": f"Token {LICENSE_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "url": audio_url,
            "callback_url": "https://myapp.com/webhook/transcription"
        }
    )

    return response.json()

if __name__ == '__main__':
    job = submit_async_transcription("https://example.com/long-audio.mp3")
    print(f"Job submitted: {job['job_id']}")

    app.run(port=5000)
```
