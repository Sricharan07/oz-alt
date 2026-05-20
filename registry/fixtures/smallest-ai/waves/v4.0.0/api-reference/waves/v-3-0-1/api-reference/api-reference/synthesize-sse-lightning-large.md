> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Text to Speech (SSE)

POST https://api.smallest.ai/waves/v1/lightning-large/stream
Content-Type: application/json

The Lightning-Large SSE API provides real-time text-to-speech streaming capabilities with high-quality voice synthesis. This API uses Server-Sent Events (SSE) to deliver audio chunks as they're generated, enabling low-latency audio playback without waiting for the entire audio file to process.

## When to Use

- **Interactive Applications**: Perfect for chatbots, virtual assistants, and other applications requiring immediate voice responses
- **Long-Form Content**: Efficiently stream audio for articles, stories, or other long-form content without buffering delays
- **Voice User Interfaces**: Create natural-sounding voice interfaces with minimal perceived latency
- **Accessibility Solutions**: Provide real-time audio versions of written content for users with visual impairments

## How It Works

1. **Make a POST Request**: Send your text and voice settings to the API endpoint
2. **Receive Audio Chunks**: The API processes your text and streams audio back as base64-encoded chunks with 1024 byte size
3. **Process the Stream**: Handle the SSE events to decode and play audio chunks sequentially
4. **End of Stream**: The API sends a completion event when all audio has been delivered

Reference: https://docs.smallest.ai/waves/v-3-0-1/api-reference/api-reference/synthesize-sse-lightning-large

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves
  version: 1.0.0
paths:
  /waves/v1/lightning-large/stream:
    post:
      operationId: synthesize-sse-lightning-large
      summary: Text to Speech (SSE)
      description: >
        The Lightning-Large SSE API provides real-time text-to-speech streaming
        capabilities with high-quality voice synthesis. This API uses
        Server-Sent Events (SSE) to deliver audio chunks as they're generated,
        enabling low-latency audio playback without waiting for the entire audio
        file to process.

        ## When to Use

        - **Interactive Applications**: Perfect for chatbots, virtual
        assistants, and other applications requiring immediate voice responses

        - **Long-Form Content**: Efficiently stream audio for articles, stories,
        or other long-form content without buffering delays

        - **Voice User Interfaces**: Create natural-sounding voice interfaces
        with minimal perceived latency

        - **Accessibility Solutions**: Provide real-time audio versions of
        written content for users with visual impairments

        ## How It Works

        1. **Make a POST Request**: Send your text and voice settings to the API
        endpoint

        2. **Receive Audio Chunks**: The API processes your text and streams
        audio back as base64-encoded chunks with 1024 byte size

        3. **Process the Stream**: Handle the SSE events to decode and play
        audio chunks sequentially

        4. **End of Stream**: The API sends a completion event when all audio
        has been delivered
      tags:
        - ''
      parameters:
        - name: Authorization
          in: header
          description: Bearer authentication
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Synthesized speech retrieved successfully.
          content:
            application/json:
              schema:
                type: object
                properties: {}
        '400':
          description: Bad request.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Synthesize_sse_lightning_largeRequestBadRequestError
        '401':
          description: Unauthorized.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Synthesize_sse_lightning_largeRequestUnauthorizedError
        '500':
          description: Server error occurred.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Synthesize_sse_lightning_largeRequestInternalServerError
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LightningLargeRequest'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    LightningLargeRequestLanguage:
      type: string
      enum:
        - en
        - hi
      default: en
      description: >-
        Determines how numbers are spelled out. If set to 'en', numbers will be
        read as individual digits in English. If set to 'hi', numbers will be
        read as individual digits in Hindi.
      title: LightningLargeRequestLanguage
    LightningLargeRequestOutputFormat:
      type: string
      enum:
        - pcm
        - mp3
        - wav
        - ulaw
        - alaw
      default: pcm
      description: The format of the output audio.
      title: LightningLargeRequestOutputFormat
    LightningLargeRequest:
      type: object
      properties:
        text:
          type: string
          description: The text to convert to speech.
        voice_id:
          type: string
          description: The voice identifier to use for speech generation.
        sample_rate:
          type: integer
          default: 24000
          description: The sample rate for the generated audio.
        speed:
          type: number
          format: double
          default: 1
          description: The speed of the generated speech.
        consistency:
          type: number
          format: double
          default: 0.5
          description: >-
            This parameter controls word repetition and skipping. Decrease it to
            prevent skipped words, and increase it to prevent repetition.
        similarity:
          type: number
          format: double
          default: 0
          description: >-
            This parameter controls the similarity between the generated speech
            and the reference audio. Increase it to make the speech more similar
            to the reference audio.
        enhancement:
          type: number
          format: double
          default: 1
          description: Enhances speech quality at the cost of increased latency.
        language:
          $ref: '#/components/schemas/LightningLargeRequestLanguage'
          default: en
          description: >-
            Determines how numbers are spelled out. If set to 'en', numbers will
            be read as individual digits in English. If set to 'hi', numbers
            will be read as individual digits in Hindi.
        output_format:
          $ref: '#/components/schemas/LightningLargeRequestOutputFormat'
          default: pcm
          description: The format of the output audio.
        pronunciation_dicts:
          type: array
          items:
            type: string
          description: >-
            The IDs of the pronunciation dictionaries to use for speech
            generation.
      required:
        - text
        - voice_id
      title: LightningLargeRequest
    Synthesize_sse_lightning_largeRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_sse_lightning_largeRequestBadRequestError
    Synthesize_sse_lightning_largeRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_sse_lightning_largeRequestUnauthorizedError
    Synthesize_sse_lightning_largeRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_sse_lightning_largeRequestInternalServerError
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-large/stream"

payload = {
    "text": "string",
    "voice_id": "string"
}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-large/stream';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"text":"string","voice_id":"string"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/lightning-large/stream"

	payload := strings.NewReader("{\n  \"text\": \"string\",\n  \"voice_id\": \"string\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer ")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/lightning-large/stream")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"text\": \"string\",\n  \"voice_id\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/lightning-large/stream")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"text\": \"string\",\n  \"voice_id\": \"string\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/waves/v1/lightning-large/stream', [
  'body' => '{
  "text": "string",
  "voice_id": "string"
}',
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-large/stream");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"text\": \"string\",\n  \"voice_id\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "text": "string",
  "voice_id": "string"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-large/stream")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```
