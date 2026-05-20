> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Lightning v3.1

POST https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech
Content-Type: application/json

Synthesize speech from text in a single request. The simplest way to get audio when you have the full text up front — pass `text` + `voice_id`, get back binary audio.

## When to use this

- **Use this** for short utterances you can render before playback (notifications, prompts, batch jobs, audio file generation).
- **Use the SSE streaming endpoint** when you want playback to start before the full audio is ready (long passages, latency-sensitive apps).
- **Use the WebSocket endpoint** when text arrives incrementally (LLM token streams, live captioning).

## Key features

- 44 kHz natural, expressive synthesis
- Cloned voice IDs (`voice_*`) work — same param as catalog voices
- 12 documented languages — see the model card for the full list
- Output formats: `pcm`, `mp3`, `wav`, `ulaw`, `alaw`
- Sample rates: 8 kHz – 44.1 kHz
- Speed: 0.5× – 2×
- Per-call pronunciation dictionaries via `pronunciation_dicts`

## Examples

**cURL**
```bash
curl -X POST "https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{
    "text": "Hello from Lightning v3.1.",
    "voice_id": "magnus",
    "sample_rate": 24000,
    "output_format": "wav"
  }' --output speech.wav
```

**Python** (`pip install smallestai>=4.4.0`)
```python
from smallestai import SmallestAI

client = SmallestAI(token="YOUR_API_KEY")

with open("speech.wav", "wb") as f:
    for chunk in client.waves.synthesize_lightning_v31(
        text="Hello from Lightning v3.1.",
        voice_id="magnus",
        sample_rate=24000,
        output_format="wav",
        # Optional: cloned voice support
        # voice_id="voice_FlPKRWI7DX",
        # Optional: pin pronunciations for specific words
        # pronunciation_dicts=[""],
    ):
        f.write(chunk)
```

**JavaScript / TypeScript** (using `fetch`)
```typescript
const res = await fetch("https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
    "Content-Type": "application/json",
    Accept: "audio/wav",
  },
  body: JSON.stringify({
    text: "Hello from Lightning v3.1.",
    voice_id: "magnus",
    sample_rate: 24000,
    output_format: "wav",
  }),
});
const audio = Buffer.from(await res.arrayBuffer());
require("node:fs").writeFileSync("speech.wav", audio);
```

## Common gotchas

- **Set `Accept: audio/wav`.** Omitting it can return an empty or unplayable response.
- **Cloned voices** (`voice_*` from `add_voice`) work on this endpoint and support `pronunciation_dicts`.
- **`pronunciation_dicts` validates IDs at request time.** Passing an unknown ID returns `Invalid input data` — create the dict first via the pronunciation-dicts endpoint and save the returned `id`.
- **Pronunciation matching is case-sensitive.** Add both `Synopsis` and `synopsis` if your text uses both casings.
- **44.1 kHz output** is supported but most playback environments are happy with 24 kHz — drop the sample rate if bandwidth matters.
- **JavaScript / TypeScript**: the official `smallestai` npm package predates Lightning v3.1, so call this endpoint with `fetch` or `axios` as shown above.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/text-to-speech/synthesize-lightning-v-31-speech

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/lightning-v3.1/get_speech:
    post:
      operationId: synthesize-lightning-v-31-speech
      summary: Lightning v3.1
      description: >
        Synthesize speech from text in a single request. The simplest way to get
        audio when you have the full text up front — pass `text` + `voice_id`,
        get back binary audio.

        ## When to use this

        - **Use this** for short utterances you can render before playback
        (notifications, prompts, batch jobs, audio file generation).

        - **Use the SSE streaming endpoint** when you want playback to start
        before the full audio is ready (long passages, latency-sensitive apps).

        - **Use the WebSocket endpoint** when text arrives incrementally (LLM
        token streams, live captioning).

        ## Key features

        - 44 kHz natural, expressive synthesis

        - Cloned voice IDs (`voice_*`) work — same param as catalog voices

        - 12 documented languages — see the model card for the full list

        - Output formats: `pcm`, `mp3`, `wav`, `ulaw`, `alaw`

        - Sample rates: 8 kHz – 44.1 kHz

        - Speed: 0.5× – 2×

        - Per-call pronunciation dictionaries via `pronunciation_dicts`

        ## Examples

        **cURL**

        ```bash

        curl -X POST
        "https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech" \
          -H "Authorization: Bearer $SMALLEST_API_KEY" \
          -H "Content-Type: application/json" \
          -H "Accept: audio/wav" \
          -d '{
            "text": "Hello from Lightning v3.1.",
            "voice_id": "magnus",
            "sample_rate": 24000,
            "output_format": "wav"
          }' --output speech.wav
        ```

        **Python** (`pip install smallestai>=4.4.0`)

        ```python

        from smallestai import SmallestAI

        client = SmallestAI(token="YOUR_API_KEY")

        with open("speech.wav", "wb") as f:
            for chunk in client.waves.synthesize_lightning_v31(
                text="Hello from Lightning v3.1.",
                voice_id="magnus",
                sample_rate=24000,
                output_format="wav",
                # Optional: cloned voice support
                # voice_id="voice_FlPKRWI7DX",
                # Optional: pin pronunciations for specific words
                # pronunciation_dicts=[""],
            ):
                f.write(chunk)
        ```

        **JavaScript / TypeScript** (using `fetch`)

        ```typescript

        const res = await
        fetch("https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
            "Content-Type": "application/json",
            Accept: "audio/wav",
          },
          body: JSON.stringify({
            text: "Hello from Lightning v3.1.",
            voice_id: "magnus",
            sample_rate: 24000,
            output_format: "wav",
          }),
        });

        const audio = Buffer.from(await res.arrayBuffer());

        require("node:fs").writeFileSync("speech.wav", audio);

        ```

        ## Common gotchas

        - **Set `Accept: audio/wav`.** Omitting it can return an empty or
        unplayable response.

        - **Cloned voices** (`voice_*` from `add_voice`) work on this endpoint
        and support `pronunciation_dicts`.

        - **`pronunciation_dicts` validates IDs at request time.** Passing an
        unknown ID returns `Invalid input data` — create the dict first via the
        pronunciation-dicts endpoint and save the returned `id`.

        - **Pronunciation matching is case-sensitive.** Add both `Synopsis` and
        `synopsis` if your text uses both casings.

        - **44.1 kHz output** is supported but most playback environments are
        happy with 24 kHz — drop the sample rate if bandwidth matters.

        - **JavaScript / TypeScript**: the official `smallestai` npm package
        predates Lightning v3.1, so call this endpoint with `fetch` or `axios`
        as shown above.
      tags:
        - subpackage_textToSpeech
      parameters:
        - name: Authorization
          in: header
          required: true
          schema:
            type: string
        - name: Accept
          in: header
          description: >-
            Must be `audio/wav` to receive binary audio. Required for proper
            playback.
          required: true
          schema:
            $ref: >-
              #/components/schemas/WavesV1LightningV31GetSpeechPostParametersAccept
      responses:
        '200':
          description: Synthesized speech retrieved successfully.
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        '400':
          description: Bad request.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SynthesizeLightningV31SpeechRequestBadRequestError
        '401':
          description: Unauthorized.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SynthesizeLightningV31SpeechRequestUnauthorizedError
        '500':
          description: Server error occurred.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SynthesizeLightningV31SpeechRequestInternalServerError
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LightningV31Request'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1LightningV31GetSpeechPostParametersAccept:
      type: string
      enum:
        - audio/wav
      default: audio/wav
      title: WavesV1LightningV31GetSpeechPostParametersAccept
    LightningV31RequestSampleRate:
      type: string
      enum:
        - '8000'
        - '16000'
        - '24000'
        - '44100'
      description: The sample rate for the generated audio.
      title: LightningV31RequestSampleRate
    LightningV31RequestLanguage:
      type: string
      enum:
        - auto
        - en
        - hi
        - mr
        - kn
        - ta
        - bn
        - gu
        - te
        - ml
        - pa
        - or
        - es
      default: en
      description: |
        Language code for synthesis. Influences pronunciation, number/date
        normalization, and phoneme selection.

        - **Indian:** `en`, `hi`, `mr` (Marathi), `kn` (Kannada), `ta` (Tamil),
          `bn` (Bengali), `gu` (Gujarati), `te` (Telugu), `ml` (Malayalam),
          `pa` (Punjabi), `or` (Odia)
        - **European:** `es` (Spanish)
        - `auto` — auto-detect from input text (recommended for code-switching)
      title: LightningV31RequestLanguage
    LightningV31RequestOutputFormat:
      type: string
      enum:
        - mp3
        - pcm
        - wav
        - ulaw
        - alaw
      default: pcm
      description: |
        Format of the returned audio. `pcm` is the lowest-latency option
        but requires a decoder to play; `mp3` and `wav` are directly
        playable in browsers and most media players. The server default
        is `pcm` when the field is omitted — the API playground uses
        `mp3` so the generated audio is directly playable.
      title: LightningV31RequestOutputFormat
    LightningV31Request:
      type: object
      properties:
        text:
          type: string
          default: Hey i am your a text to speech model
          description: The text to convert to speech.
        voice_id:
          type: string
          default: daniel
          description: The voice identifier to use for speech generation.
        sample_rate:
          $ref: '#/components/schemas/LightningV31RequestSampleRate'
          default: 44100
          description: The sample rate for the generated audio.
        speed:
          type: number
          format: double
          default: 1
          description: The speed of the generated speech.
        language:
          $ref: '#/components/schemas/LightningV31RequestLanguage'
          default: en
          description: >
            Language code for synthesis. Influences pronunciation, number/date

            normalization, and phoneme selection.

            - **Indian:** `en`, `hi`, `mr` (Marathi), `kn` (Kannada), `ta`
            (Tamil),
              `bn` (Bengali), `gu` (Gujarati), `te` (Telugu), `ml` (Malayalam),
              `pa` (Punjabi), `or` (Odia)
            - **European:** `es` (Spanish)

            - `auto` — auto-detect from input text (recommended for
            code-switching)
        output_format:
          $ref: '#/components/schemas/LightningV31RequestOutputFormat'
          default: pcm
          description: |
            Format of the returned audio. `pcm` is the lowest-latency option
            but requires a decoder to play; `mp3` and `wav` are directly
            playable in browsers and most media players. The server default
            is `pcm` when the field is omitted — the API playground uses
            `mp3` so the generated audio is directly playable.
        pronunciation_dicts:
          type: array
          items:
            type: string
          description: >-
            The IDs of the pronunciation dictionaries to use for speech
            generation.
        session_id:
          type: string
          description: >-
            Optional client-provided session identifier for correlation. Only
            alphanumeric characters, hyphens, underscores, and dots are allowed.
            Max 128 characters. Echoed back in response headers as
            `X-External-Session-Id`.
        request_id:
          type: string
          description: >-
            Optional client-provided request identifier for correlation. Only
            alphanumeric characters, hyphens, underscores, and dots are allowed.
            Max 128 characters. Echoed back in response headers as
            `X-External-Request-Id`.
      required:
        - text
        - voice_id
      title: LightningV31Request
    SynthesizeLightningV31SpeechRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: SynthesizeLightningV31SpeechRequestBadRequestError
    SynthesizeLightningV31SpeechRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: SynthesizeLightningV31SpeechRequestUnauthorizedError
    SynthesizeLightningV31SpeechRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: SynthesizeLightningV31SpeechRequestInternalServerError
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech"

payload = {
    "text": "Hey i am your a text to speech model",
    "voice_id": "daniel",
    "sample_rate": 44100,
    "speed": 1,
    "output_format": "mp3"
}
headers = {
    "Accept": "audio/wav",
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech';
const options = {
  method: 'POST',
  headers: {
    Accept: 'audio/wav',
    Authorization: 'Bearer ',
    'Content-Type': 'application/json'
  },
  body: '{"text":"Hey i am your a text to speech model","voice_id":"daniel","sample_rate":44100,"speed":1,"output_format":"mp3"}'
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

	url := "https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech"

	payload := strings.NewReader("{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"daniel\",\n  \"sample_rate\": 44100,\n  \"speed\": 1,\n  \"output_format\": \"mp3\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Accept", "audio/wav")
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

url = URI("https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Accept"] = 'audio/wav'
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"daniel\",\n  \"sample_rate\": 44100,\n  \"speed\": 1,\n  \"output_format\": \"mp3\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech")
  .header("Accept", "audio/wav")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"daniel\",\n  \"sample_rate\": 44100,\n  \"speed\": 1,\n  \"output_format\": \"mp3\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech', [
  'body' => '{
  "text": "Hey i am your a text to speech model",
  "voice_id": "daniel",
  "sample_rate": 44100,
  "speed": 1,
  "output_format": "mp3"
}',
  'headers' => [
    'Accept' => 'audio/wav',
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech");
var request = new RestRequest(Method.POST);
request.AddHeader("Accept", "audio/wav");
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"daniel\",\n  \"sample_rate\": 44100,\n  \"speed\": 1,\n  \"output_format\": \"mp3\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Accept": "audio/wav",
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "text": "Hey i am your a text to speech model",
  "voice_id": "daniel",
  "sample_rate": 44100,
  "speed": 1,
  "output_format": "mp3"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-v3.1/get_speech")! as URL,
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
