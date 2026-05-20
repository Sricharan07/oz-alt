> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Pulse (Pre-Recorded)

POST https://api.smallest.ai/waves/v1/pulse/get_text
Content-Type: application/octet-stream

Transcribe an audio file to text using the Pulse model. The fastest way to get a transcript when you already have a recording — pass either the raw bytes or a URL.

## When to use this

Use this endpoint when you have a complete audio file (call recording, voicemail, podcast episode) and want the transcript back in one response. For live transcription as audio arrives, use the realtime WebSocket endpoint (`WSS /waves/v1/pulse/get_text`) instead.

## Input methods

Send the audio in one of two ways:

1. **Raw bytes** — `Content-Type: application/octet-stream` with the audio in the body. All knobs (`language`, `word_timestamps`, etc.) are query parameters.
2. **URL** — `Content-Type: application/json` with `{"url": "..."}` in the body. Useful when the audio already lives in object storage. Same query parameters apply.

Pulse autodetects the language across 30+ supported locales. Pass `language` explicitly when you already know it — detection is fast but skipping it is faster.

## Examples

**cURL** (raw bytes)
```bash
curl -X POST "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&word_timestamps=true" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@./call.wav"
```

**cURL** (URL)
```bash
curl -X POST "https://api.smallest.ai/waves/v1/pulse/get_text?language=en" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-bucket.s3.amazonaws.com/call.wav"}'
```

**Python** (`pip install smallestai>=4.4.0`)
```python
from smallestai import SmallestAI

client = SmallestAI(token="YOUR_API_KEY")
with open("./call.wav", "rb") as f:
    result = client.waves.transcribe_pulse(
        request=f.read(),
        language="en",
        word_timestamps=True,
        diarize=True,
    )
print(result.status)         # "success"
print(result.transcription)  # the transcript string
```

**JavaScript / TypeScript** (using `fetch`)
```typescript
import { readFileSync } from "node:fs";

const audio = readFileSync("./call.wav");
const params = new URLSearchParams({ language: "en", word_timestamps: "true", diarize: "true" });

const res = await fetch(`https://api.smallest.ai/waves/v1/pulse/get_text?${params}`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
    "Content-Type": "application/octet-stream",
  },
  body: audio,
});
const result = await res.json();
console.log(result.transcription);
```

## Common gotchas

- **Max file size is 25 MB.** Larger files return HTTP `413`. Compress to mono 16 kHz PCM if you're close to the limit; quality is unaffected.
- **Formatting flags (`format`, `punctuate`, `capitalize`)** are accepted at the wire level and exposed in the Python SDK as of `smallestai>=4.4.0`. Today they currently return the same transcript regardless of value — pass them in your integration so it works as the behavior changes.
- **Webhook-driven flow**: pass `webhook_url` to receive the transcript asynchronously. The endpoint returns immediately; the transcript hits your webhook when ready. Useful for long files where you don't want to hold an HTTP connection open.
- **Speaker diarization** (`diarize=true`) adds latency. Skip it if you only need the words.
- **JavaScript / TypeScript**: the official `smallestai` npm package predates the Pulse model, so call this endpoint with `fetch` or `axios` as shown above.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/speech-to-text/pulse-speech-to-text

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/pulse/get_text:
    post:
      operationId: pulse-speech-to-text
      summary: Pulse (Pre-Recorded)
      description: >
        Transcribe an audio file to text using the Pulse model. The fastest way
        to get a transcript when you already have a recording — pass either the
        raw bytes or a URL.

        ## When to use this

        Use this endpoint when you have a complete audio file (call recording,
        voicemail, podcast episode) and want the transcript back in one
        response. For live transcription as audio arrives, use the realtime
        WebSocket endpoint (`WSS /waves/v1/pulse/get_text`) instead.

        ## Input methods

        Send the audio in one of two ways:

        1. **Raw bytes** — `Content-Type: application/octet-stream` with the
        audio in the body. All knobs (`language`, `word_timestamps`, etc.) are
        query parameters.

        2. **URL** — `Content-Type: application/json` with `{"url": "..."}` in
        the body. Useful when the audio already lives in object storage. Same
        query parameters apply.

        Pulse autodetects the language across 30+ supported locales. Pass
        `language` explicitly when you already know it — detection is fast but
        skipping it is faster.

        ## Examples

        **cURL** (raw bytes)

        ```bash

        curl -X POST
        "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&word_timestamps=true"
        \
          -H "Authorization: Bearer $SMALLEST_API_KEY" \
          -H "Content-Type: application/octet-stream" \
          --data-binary "@./call.wav"
        ```

        **cURL** (URL)

        ```bash

        curl -X POST
        "https://api.smallest.ai/waves/v1/pulse/get_text?language=en" \
          -H "Authorization: Bearer $SMALLEST_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{"url": "https://your-bucket.s3.amazonaws.com/call.wav"}'
        ```

        **Python** (`pip install smallestai>=4.4.0`)

        ```python

        from smallestai import SmallestAI

        client = SmallestAI(token="YOUR_API_KEY")

        with open("./call.wav", "rb") as f:
            result = client.waves.transcribe_pulse(
                request=f.read(),
                language="en",
                word_timestamps=True,
                diarize=True,
            )
        print(result.status)         # "success"

        print(result.transcription)  # the transcript string

        ```

        **JavaScript / TypeScript** (using `fetch`)

        ```typescript

        import { readFileSync } from "node:fs";

        const audio = readFileSync("./call.wav");

        const params = new URLSearchParams({ language: "en", word_timestamps:
        "true", diarize: "true" });

        const res = await
        fetch(`https://api.smallest.ai/waves/v1/pulse/get_text?${params}`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
            "Content-Type": "application/octet-stream",
          },
          body: audio,
        });

        const result = await res.json();

        console.log(result.transcription);

        ```

        ## Common gotchas

        - **Max file size is 25 MB.** Larger files return HTTP `413`. Compress
        to mono 16 kHz PCM if you're close to the limit; quality is unaffected.

        - **Formatting flags (`format`, `punctuate`, `capitalize`)** are
        accepted at the wire level and exposed in the Python SDK as of
        `smallestai>=4.4.0`. Today they currently return the same transcript
        regardless of value — pass them in your integration so it works as the
        behavior changes.

        - **Webhook-driven flow**: pass `webhook_url` to receive the transcript
        asynchronously. The endpoint returns immediately; the transcript hits
        your webhook when ready. Useful for long files where you don't want to
        hold an HTTP connection open.

        - **Speaker diarization** (`diarize=true`) adds latency. Skip it if you
        only need the words.

        - **JavaScript / TypeScript**: the official `smallestai` npm package
        predates the Pulse model, so call this endpoint with `fetch` or `axios`
        as shown above.
      tags:
        - subpackage_speechToText
      parameters:
        - name: language
          in: query
          description: >
            Language of the audio file. Set explicitly to the known language for
            best accuracy.

            Auto-detection scopes:

            - `multi-eu` (default) — European set: de, en, fr, it, nl, pt, ru,
            es.

            - `multi-indic` — Indic set: en, hi, mr, pa, gu, or, ka, ta, te, ml,
            bn.

            - `multi-asian` — East Asian set: en, ja, ko, zh, yue.

            - `multi` — full multilingual auto-detection across all supported
            languages.

            Omitting `language` routes to `multi-eu`, which can mis-detect on
            non-European audio. Always pass `language` explicitly when the
            source language is known, or pick the regional `multi-*` scope that
            matches your audio.
          required: false
          schema:
            $ref: '#/components/schemas/WavesV1PulseGetTextPostParametersLanguage'
            default: multi-eu
        - name: encoding
          in: query
          description: |
            Audio encoding of the bytes you upload. Mirrors the `encoding`
            parameter on the realtime WS endpoint.

            - `linear16`, `linear32` — raw PCM (16-bit and 32-bit)
            - `alaw`, `mulaw` — 8 kHz telephony codecs
            - `opus`, `ogg_opus` — Opus compressed audio (raw and Ogg container)

            When omitted, the server detects the format from the file's
            container header (works for `.wav`, `.mp3`, `.flac`, `.ogg`,
            `.m4a`, `.webm`).
          required: false
          schema:
            $ref: '#/components/schemas/WavesV1PulseGetTextPostParametersEncoding'
        - name: webhook_url
          in: query
          required: false
          schema:
            type: string
            format: uri
        - name: webhook_extra
          in: query
          required: false
          schema:
            type: string
        - name: word_timestamps
          in: query
          description: >-
            Whether to include word and utterance level timestamps in the
            response
          required: false
          schema:
            type: boolean
            default: false
        - name: diarize
          in: query
          description: Whether to perform speaker diarization
          required: false
          schema:
            type: boolean
            default: false
        - name: gender_detection
          in: query
          description: Whether to predict the gender of the speaker
          required: false
          schema:
            $ref: >-
              #/components/schemas/WavesV1PulseGetTextPostParametersGenderDetection
            default: 'false'
        - name: emotion_detection
          in: query
          description: Whether to predict speaker emotions
          required: false
          schema:
            $ref: >-
              #/components/schemas/WavesV1PulseGetTextPostParametersEmotionDetection
            default: 'false'
        - name: format
          in: query
          description: |
            Master formatting switch for the transcript. When `false`, forces
            `punctuate=false`, `capitalize=false`, and also disables Inverse
            Text Normalization (ITN) so it cannot silently reintroduce
            punctuation or casing.

            When `true`, the `punctuate` and `capitalize` params take effect
            independently. Leave `format=true` and use those two to fine-tune.
          required: false
          schema:
            $ref: '#/components/schemas/WavesV1PulseGetTextPostParametersFormat'
            default: 'true'
        - name: punctuate
          in: query
          description: >
            When `false`, strips end-of-sentence punctuation (`.`, `,`, `?`,
            `!`)

            from the transcript, `words[].word`, and

            `utterances[].transcript`. Does not affect casing — use

            `capitalize` for that. Overridden to `false` when `format=false`.
          required: false
          schema:
            $ref: '#/components/schemas/WavesV1PulseGetTextPostParametersPunctuate'
            default: 'true'
        - name: capitalize
          in: query
          description: |
            When `false`, lowercases the entire transcript output (transcript,
            `words[].word`, and `utterances[].transcript`). Does not affect
            punctuation — use `punctuate` for that. Overridden to `false`
            when `format=false`.
          required: false
          schema:
            $ref: '#/components/schemas/WavesV1PulseGetTextPostParametersCapitalize'
            default: 'true'
        - name: Authorization
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Speech transcribed successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Speech to
                  Text_pulseSpeechToText_Response_200
        '400':
          description: Bad request - Invalid parameters or file format
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized - Invalid or missing authentication
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '413':
          description: Payload too large - File size exceeds limit
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '429':
          description: Too many requests - Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
      requestBody:
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1PulseGetTextPostParametersLanguage:
      type: string
      enum:
        - it
        - es
        - en
        - pt
        - hi
        - de
        - fr
        - uk
        - ru
        - kn
        - ml
        - pl
        - mr
        - gu
        - cs
        - sk
        - te
        - or
        - nl
        - bn
        - lv
        - et
        - ro
        - pa
        - fi
        - sv
        - bg
        - ta
        - hu
        - da
        - lt
        - mt
        - multi
        - multi-eu
        - multi-indic
        - multi-asian
      default: multi-eu
      title: WavesV1PulseGetTextPostParametersLanguage
    WavesV1PulseGetTextPostParametersEncoding:
      type: string
      enum:
        - linear16
        - linear32
        - alaw
        - mulaw
        - opus
        - ogg_opus
      title: WavesV1PulseGetTextPostParametersEncoding
    WavesV1PulseGetTextPostParametersGenderDetection:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      title: WavesV1PulseGetTextPostParametersGenderDetection
    WavesV1PulseGetTextPostParametersEmotionDetection:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      title: WavesV1PulseGetTextPostParametersEmotionDetection
    WavesV1PulseGetTextPostParametersFormat:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      title: WavesV1PulseGetTextPostParametersFormat
    WavesV1PulseGetTextPostParametersPunctuate:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      title: WavesV1PulseGetTextPostParametersPunctuate
    WavesV1PulseGetTextPostParametersCapitalize:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      title: WavesV1PulseGetTextPostParametersCapitalize
    WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaWordsItems:
      type: object
      properties:
        start:
          type: number
          format: double
        end:
          type: number
          format: double
        speaker:
          type: string
          description: Speaker if diarization is enabled
        word:
          type: string
      title: WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaWordsItems
    WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaUtterancesItems:
      type: object
      properties:
        text:
          type: string
        start:
          type: number
          format: double
        end:
          type: number
          format: double
        speaker:
          type: string
          description: Speaker if diarization is enabled
      title: >-
        WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaUtterancesItems
    WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaGender:
      type: string
      enum:
        - male
        - female
      description: Predicted gender of the speaker if requested
      title: WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaGender
    WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaEmotions:
      type: object
      properties:
        happiness:
          type: number
          format: double
        sadness:
          type: number
          format: double
        disgust:
          type: number
          format: double
        fear:
          type: number
          format: double
        anger:
          type: number
          format: double
      description: Predicted emotions of the speaker if requested
      title: WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaEmotions
    WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaMetadata:
      type: object
      properties:
        filename:
          type: string
          description: Name of the audio file
        duration:
          type: number
          format: double
          description: Duration of the audio file in minutes
        fileSize:
          type: number
          format: double
          description: Size of the audio file in bytes
      description: Metadata about the transcription
      title: WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaMetadata
    Speech to Text_pulseSpeechToText_Response_200:
      type: object
      properties:
        status:
          type: string
          description: Status of the transcription request
        transcription:
          type: string
          description: The transcribed text from the audio file
        audio_length:
          type: number
          format: double
          description: Duration of the audio file in seconds
        words:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaWordsItems
          description: Word-level timestamps in seconds.
        utterances:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaUtterancesItems
          description: List of utterances with start and end times
        gender:
          $ref: >-
            #/components/schemas/WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaGender
          description: Predicted gender of the speaker if requested
        emotions:
          $ref: >-
            #/components/schemas/WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaEmotions
          description: Predicted emotions of the speaker if requested
        metadata:
          $ref: >-
            #/components/schemas/WavesV1PulseGetTextPostResponsesContentApplicationJsonSchemaMetadata
          description: Metadata about the transcription
      title: Speech to Text_pulseSpeechToText_Response_200
    ErrorResponseStatus:
      type: string
      enum:
        - error
      title: ErrorResponseStatus
    ErrorResponseError:
      type: object
      properties:
        message:
          type: string
        code:
          type: string
      title: ErrorResponseError
    ErrorResponse:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/ErrorResponseStatus'
        error:
          $ref: '#/components/schemas/ErrorResponseError'
      title: ErrorResponse
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python Speech to Text_pulseSpeechToText_example
import requests

url = "https://api.smallest.ai/waves/v1/pulse/get_text"

headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/octet-stream"
}

response = requests.post(url, headers=headers)

print(response.json())
```

```javascript Speech to Text_pulseSpeechToText_example
const url = 'https://api.smallest.ai/waves/v1/pulse/get_text';
const options = {
  method: 'POST',
  headers: {
    Authorization: 'Bearer ',
    'Content-Type': 'application/octet-stream'
  }
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Speech to Text_pulseSpeechToText_example
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/pulse/get_text"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("Authorization", "Bearer ")
	req.Header.Add("Content-Type", "application/octet-stream")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Speech to Text_pulseSpeechToText_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/pulse/get_text")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/octet-stream'

response = http.request(request)
puts response.read_body
```

```java Speech to Text_pulseSpeechToText_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/pulse/get_text")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/octet-stream")
  .asString();
```

```php Speech to Text_pulseSpeechToText_example
request('POST', 'https://api.smallest.ai/waves/v1/pulse/get_text', [
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/octet-stream',
  ],
]);

echo $response->getBody();
```

```csharp Speech to Text_pulseSpeechToText_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/pulse/get_text");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/octet-stream");
IRestResponse response = client.Execute(request);
```

```swift Speech to Text_pulseSpeechToText_example
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/octet-stream"
]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/pulse/get_text")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers

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
