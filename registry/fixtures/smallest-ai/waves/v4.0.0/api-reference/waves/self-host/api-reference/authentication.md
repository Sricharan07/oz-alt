> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Authentication

> Authenticate API requests with your license key

## Overview

All API requests to Smallest Self-Host require authentication using your license key. This ensures only authorized clients can access the speech-to-text service.

## Authentication Method

Smallest Self-Host uses **Bearer token authentication** with your license key.

### Authorization Header

Include your license key in the `Authorization` header:

```http
Authorization: Token YOUR_LICENSE_KEY
```

## Example Requests

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

LICENSE_KEY = "your-license-key-here"
API_URL = "http://localhost:7100"

headers = {
    "Authorization": f"Token {LICENSE_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_URL}/v1/listen",
    headers=headers,
    json={"url": "https://example.com/audio.wav"}
)

print(response.json())
```

```javascript
const LICENSE_KEY = "your-license-key-here";
const API_URL = "http://localhost:7100";

const response = await fetch(`${API_URL}/v1/listen`, {
  method: "POST",
  headers: {
    "Authorization": `Token ${LICENSE_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    url: "https://example.com/audio.wav"
  })
});

const result = await response.json();
console.log(result);
```

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

func main() {
    licenseKey := "your-license-key-here"
    apiURL := "http://localhost:7100/v1/listen"

    payload := map[string]string{
        "url": "https://example.com/audio.wav",
    }
    jsonData, _ := json.Marshal(payload)

    req, _ := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonData))
    req.Header.Set("Authorization", "Token "+licenseKey)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    fmt.Println(result)
}
```

## Response Codes

        Code

        Status

        Description

        200

        OK

        Request successful

        400

        Bad Request

        Invalid request parameters

        401

        Unauthorized

        Invalid or missing license key

        403

        Forbidden

        License expired or quota exceeded

        429

        Too Many Requests

        Rate limit exceeded

        500

        Internal Server Error

        Server error

        503

        Service Unavailable

        Service temporarily unavailable

## Error Responses

### 401 Unauthorized

```json
{
  "error": "Invalid license key",
  "code": "INVALID_LICENSE"
}
```

**Solutions**:

* Verify license key is correct
* Check Authorization header format
* Ensure license hasn't expired

### 403 Forbidden

```json
{
  "error": "License expired",
  "code": "LICENSE_EXPIRED",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Solutions**:

* Renew license with Smallest.ai
* Contact [support@smallest.ai](mailto:support@smallest.ai)

### 429 Rate Limited

```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

**Solutions**:

* Wait and retry after specified seconds
* Implement exponential backoff
* Contact support for higher limits

## Security Best Practices

Never hardcode license keys in source code.

**Use environment variables**:

```bash
export LICENSE_KEY="your-license-key-here"
```

**Or secret managers**:

* AWS Secrets Manager
* HashiCorp Vault
* Kubernetes Secrets

Always use HTTPS for API requests in production:

```javascript
const API_URL = "https://api.example.com";
```

Configure TLS:

```yaml
apiServer:
  tls:
    enabled: true
    certSecretName: "api-server-tls"
```

Implement key rotation policy:

* Rotate keys every 90 days
* Use different keys for dev/staging/prod
* Revoke compromised keys immediately

Track API usage to detect anomalies:

* Unusual traffic patterns
* Failed authentication attempts
* Quota approaching limits

Add client-side rate limiting:

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)
def call_api():
    response = requests.post(...)
    return response
```

## SDK Integration

### Python SDK

```bash
pip install smallest-client
```

```python
from smallest import Client

client = Client(
    api_url="http://localhost:7100",
    license_key="your-license-key-here"
)

result = client.transcribe_url("https://example.com/audio.wav")
print(result.text)
```

### JavaScript SDK

```bash
npm install @smallest/client
```

```javascript
import { SmallestClient } from '@smallest/client';

const client = new SmallestClient({
  apiUrl: 'http://localhost:7100',
  licenseKey: 'your-license-key-here'
});

const result = await client.transcribeUrl('https://example.com/audio.wav');
console.log(result.text);
```

SDKs automatically handle authentication, retries, and error handling.

## Testing Authentication

### Health Check (No Auth Required)

```bash
curl http://localhost:7100/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

### Verify License Key

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/test.wav"}'
```

Successful authentication returns transcription results.

## What's Next?

Learn about the transcription API

Monitor service health

See complete integration examples
