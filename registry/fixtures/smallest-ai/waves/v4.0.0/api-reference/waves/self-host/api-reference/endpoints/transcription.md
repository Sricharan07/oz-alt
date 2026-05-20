> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Transcription

> Convert speech to text with the /v1/listen endpoint

## Overview

The transcription endpoint converts audio files to text using Lightning ASR. Supports both batch processing and streaming.

## Endpoint

```
POST /v1/listen
```

## Authentication

Requires Bearer token authentication with your license key.

```http
Authorization: Token YOUR_LICENSE_KEY
```

See [Authentication](/waves/self-host/api-reference/authentication) for details.

## Request

### From URL

Transcribe audio from a publicly accessible URL:

```json
{
  "url": "https://example.com/audio.wav"
}
```

### From File Upload

Upload audio directly:

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -F "audio=@/path/to/audio.wav"
```

### Parameters

URL to audio file (mutually exclusive with file upload)

Supported protocols: `http://`, `https://`, `s3://`

Audio file upload (mutually exclusive with URL)

Supported formats: WAV, MP3, FLAC, OGG, M4A

Language code (ISO 639-1)

Examples: `en`, `es`, `fr`, `de`, `zh`

Add punctuation to transcript

Enable speaker diarization (identify different speakers)

Expected number of speakers (for diarization)

If not specified, automatically detected

Include word-level timestamps

Webhook URL for async results delivery

If provided, returns immediately with job ID

## Response

### Successful Response

```json
{
  "request_id": "req_abc123",
  "text": "Hello, this is a sample transcription.",
  "confidence": 0.95,
  "duration": 3.2,
  "language": "en",
  "words": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5,
      "confidence": 0.98
    },
    {
      "word": "this",
      "start": 0.6,
      "end": 0.8,
      "confidence": 0.97
    }
  ]
}
```

### Response Fields

Unique identifier for this transcription request

Complete transcription text

Overall confidence score (0.0 to 1.0)

Audio duration in seconds

Detected or specified language

Word-level details (if `timestamps: true`)

Each word object contains:

* `word`: The word text
* `start`: Start time in seconds
* `end`: End time in seconds
* `confidence`: Word confidence score

## Examples

### Basic Transcription

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/audio.wav"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:7100/v1/listen",
    headers={
        "Authorization": f"Token {LICENSE_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "url": "https://example.com/audio.wav"
    }
)

result = response.json()
print(result['text'])
```

```javascript
const response = await fetch('http://localhost:7100/v1/listen', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${LICENSE_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com/audio.wav'
  })
});

const result = await response.json();
console.log(result.text);
```

### With Punctuation and Timestamps

```json
{
  "url": "https://example.com/audio.wav",
  "punctuate": true,
  "timestamps": true
}
```

Response:

```json
{
  "request_id": "req_abc123",
  "text": "Hello, this is a sample transcription.",
  "confidence": 0.95,
  "duration": 3.2,
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98},
    {"word": ",", "start": 0.5, "end": 0.5, "confidence": 1.0},
    {"word": "this", "start": 0.6, "end": 0.8, "confidence": 0.97}
  ]
}
```

### With Speaker Diarization

```json
{
  "url": "https://example.com/conversation.wav",
  "diarize": true,
  "num_speakers": 2
}
```

Response:

```json
{
  "request_id": "req_abc123",
  "text": "Hello. Hi there!",
  "speakers": [
    {
      "speaker": "SPEAKER_00",
      "text": "Hello.",
      "start": 0.0,
      "end": 0.8
    },
    {
      "speaker": "SPEAKER_01",
      "text": "Hi there!",
      "start": 1.0,
      "end": 1.8
    }
  ]
}
```

### File Upload

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -F "audio=@recording.wav" \
  -F "punctuate=true" \
  -F "language=en"
```

### Async with Callback

```json
{
  "url": "https://example.com/long-audio.wav",
  "callback_url": "https://myapp.com/webhook/transcription"
}
```

Immediate response:

```json
{
  "job_id": "job_xyz789",
  "status": "processing"
}
```

Later, webhook receives:

```json
{
  "job_id": "job_xyz789",
  "status": "completed",
  "result": {
    "text": "...",
    "confidence": 0.95
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Missing required parameter: url or audio file",
  "code": "MISSING_PARAMETER"
}
```

### 415 Unsupported Media Type

```json
{
  "error": "Unsupported audio format",
  "code": "UNSUPPORTED_FORMAT",
  "supported_formats": ["wav", "mp3", "flac", "ogg", "m4a"]
}
```

### 422 Unprocessable Entity

```json
{
  "error": "Audio file too large",
  "code": "FILE_TOO_LARGE",
  "max_size_mb": 100
}
```

### 503 Service Unavailable

```json
{
  "error": "No ASR workers available",
  "code": "SERVICE_UNAVAILABLE",
  "retry_after": 30
}
```

## Audio Format Requirements

### Supported Formats

        Format

        Extension

        Notes

        WAV

        .wav

        Recommended for best quality

        MP3

        .mp3

        Widely supported

        FLAC

        .flac

        Lossless compression

        OGG

        .ogg

        Open format

        M4A

        .m4a

        Apple format

### Recommended Specifications

* **Sample Rate**: 16 kHz or higher (44.1 kHz recommended)
* **Bit Depth**: 16-bit or higher
* **Channels**: Mono or stereo
* **Max Duration**: 2 hours
* **Max File Size**: 100 MB

### Audio Preprocessing

For best results:

* Remove background noise
* Normalize audio levels
* Use mono audio when possible
* Encode at 16 kHz or 44.1 kHz

## Rate Limits

Default rate limits:

* **Requests per minute**: 60
* **Concurrent requests**: 10
* **Audio hours per day**: 100

Contact [support@smallest.ai](mailto:support@smallest.ai) to increase limits for your license.

## Performance

Typical performance metrics:

        Metric

        Value

        Real-time Factor

        0.05-0.15x

        Latency (1 min audio)

        3-9 seconds

        Concurrent capacity

        100+ requests

        Throughput

        100+ hours/hour

Performance varies based on:

* Audio duration and complexity
* Number of speakers
* GPU instance type
* Current load

## Best Practices

* Use lossless formats (WAV, FLAC) when possible
* Ensure clear audio with minimal background noise
* Use appropriate sample rate (16 kHz minimum)

Implement retry logic with exponential backoff:

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
```

For audio longer than 5 minutes, use callback URL:

```json
{
  "url": "https://example.com/podcast.mp3",
  "callback_url": "https://myapp.com/webhook"
}
```

Cache transcription results to avoid duplicate processing:

```python
import hashlib

def get_cache_key(audio_url):
    return hashlib.md5(audio_url.encode()).hexdigest()

cache_key = get_cache_key(audio_url)
if cache_key in cache:
    return cache[cache_key]

result = transcribe(audio_url)
cache[cache_key] = result
return result
```

## What's Next?

Monitor service availability

Complete integration examples
