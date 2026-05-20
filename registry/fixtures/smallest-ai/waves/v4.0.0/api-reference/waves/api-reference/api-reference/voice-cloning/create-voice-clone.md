> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create a Voice Clone

POST https://api.smallest.ai/waves/v1/voice-cloning
Content-Type: multipart/form-data

Create an instant voice clone in a single call. Defaults to `lightning-v3.1`.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/voice-cloning/create-voice-clone

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/voice-cloning:
    post:
      operationId: create-voice-clone
      summary: Create a Voice Clone
      description: >
        Create an instant voice clone in a single call. Defaults to
        `lightning-v3.1`.
      tags:
        - subpackage_voiceCloning
      parameters:
        - name: Authorization
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: >-
            Voice clone created. Includes pre-generated sample clips of the new
            voice.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Voice
                  Cloning_createVoiceClone_Response_200
        '400':
          description: >
            Validation error. Common causes: no file provided, invalid MIME
            type,

            file too large, clone limit exceeded, invalid language, or

            `model=lightning-v2` (deprecated).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateVoiceCloneRequestBadRequestError'
        '401':
          description: Unauthorized — missing or invalid API key.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateVoiceCloneRequestUnauthorizedError'
        '500':
          description: >-
            Server error. The `error_code` field may be populated for known
            failure modes.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/CreateVoiceCloneRequestInternalServerError
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                displayName:
                  type: string
                  description: Human-readable name for the voice clone.
                file:
                  type: string
                  format: binary
                  description: |
                    Audio file to clone from. Supported MIME types:
                    `audio/mpeg`, `audio/mpeg-3`, `audio/wav`, `audio/wave`,
                    `audio/webm`, `video/webm`, `audio/mp4`, `video/mp4`.
                    Maximum size: 5 MB.
                description:
                  type: string
                  description: Optional longer description for the voice clone.
                accent:
                  type: string
                  description: Optional accent tag (e.g. "general", "indian").
                tags:
                  type: string
                  description: >
                    Optional comma-separated list of tags. Server splits on

                    commas and trims whitespace (`"en, tone-test"` → `["en",
                    "tone-test"]`).
                language:
                  type: string
                  description: >
                    Primary language the clone will be used for. Optional, but

                    **strongly recommended** — set it to the language of your

                    reference audio. When a TTS request later uses

                    `language: "auto"`, the server falls back to this value, so

                    setting it now avoids silent language mismatches at
                    inference

                    time.

                    Must be one of the languages supported by `lightning-v3.1`

                    (e.g. `en`, `hi`, `multi`). The server validates and rejects

                    unsupported codes with a 400.
                model:
                  $ref: >-
                    #/components/schemas/WavesV1VoiceCloningPostRequestBodyContentMultipartFormDataSchemaModel
                  default: lightning-v3.1
                  description: >
                    Voice cloning model. Defaults to `lightning-v3.1`.

                    `lightning-v2` is accepted by the schema for historical

                    reasons but is deprecated — the server returns 400 with

                    `"Voice cloning for lightning-v2 is deprecated. Please use
                    lightning-v3.1"`.
              required:
                - displayName
                - file
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1VoiceCloningPostRequestBodyContentMultipartFormDataSchemaModel:
      type: string
      enum:
        - lightning-v3.1
      default: lightning-v3.1
      description: >
        Voice cloning model. Defaults to `lightning-v3.1`.

        `lightning-v2` is accepted by the schema for historical

        reasons but is deprecated — the server returns 400 with

        `"Voice cloning for lightning-v2 is deprecated. Please use
        lightning-v3.1"`.
      title: WavesV1VoiceCloningPostRequestBodyContentMultipartFormDataSchemaModel
    WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataStatus:
      type: string
      enum:
        - pending
        - processing
        - completed
        - failed
      title: WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataStatus
    WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataSamplesItems:
      type: object
      properties:
        text:
          type: string
          description: Text that was synthesized.
        audioUrl:
          type: string
          description: Signed URL to the generated sample audio.
      title: >-
        WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataSamplesItems
    WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        voiceId:
          type: string
          description: Unique voice ID. Pass this as `voice_id` in TTS requests.
        displayName:
          type: string
        model:
          type: string
          description: Internal model document for the cloned voice.
        status:
          $ref: >-
            #/components/schemas/WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataStatus
        language:
          type: string
        audioFileNames:
          type: array
          items:
            type: string
        createdAt:
          type: string
          format: date-time
        organizationId:
          type: string
        samples:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataSamplesItems
          description: Pre-generated sample audio clips in the cloned voice.
      title: WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaData
    Voice Cloning_createVoiceClone_Response_200:
      type: object
      properties:
        message:
          type: string
        data:
          $ref: >-
            #/components/schemas/WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaData
      title: Voice Cloning_createVoiceClone_Response_200
    CreateVoiceCloneRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error message.
      title: CreateVoiceCloneRequestBadRequestError
    CreateVoiceCloneRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
      title: CreateVoiceCloneRequestUnauthorizedError
    WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaErrorCode:
      type: string
      enum:
        - voice_clone_timeout
        - voice_clone_error
      description: Present when a known failure mode occurred.
      title: WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaErrorCode
    CreateVoiceCloneRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
        error_code:
          $ref: >-
            #/components/schemas/WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaErrorCode
          description: Present when a known failure mode occurred.
      title: CreateVoiceCloneRequestInternalServerError
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/voice-cloning"

files = { "file": "open('emma_watson_sample.wav', 'rb')" }
payload = {
    "displayName": "Emma Watson Clone",
    "description": ,
    "accent": ,
    "tags": ,
    "language": ,
    "model":
}
headers = {"Authorization": "Bearer "}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/voice-cloning';
const form = new FormData();
form.append('displayName', 'Emma Watson Clone');
form.append('file', 'emma_watson_sample.wav');
form.append('description', '');
form.append('accent', '');
form.append('tags', '');
form.append('language', '');
form.append('model', '');

const options = {method: 'POST', headers: {Authorization: 'Bearer '}};

options.body = form;

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

	url := "https://api.smallest.ai/waves/v1/voice-cloning"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nEmma Watson Clone\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"emma_watson_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer ")

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

url = URI("https://api.smallest.ai/waves/v1/voice-cloning")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nEmma Watson Clone\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"emma_watson_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/voice-cloning")
  .header("Authorization", "Bearer ")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nEmma Watson Clone\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"emma_watson_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/waves/v1/voice-cloning', [
  'multipart' => [
    [
        'name' => 'displayName',
        'contents' => 'Emma Watson Clone'
    ],
    [
        'name' => 'file',
        'filename' => 'emma_watson_sample.wav',
        'contents' => null
    ]
  ]
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/voice-cloning");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nEmma Watson Clone\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"emma_watson_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]
let parameters = [
  [
    "name": "displayName",
    "value": "Emma Watson Clone"
  ],
  [
    "name": "file",
    "fileName": "emma_watson_sample.wav"
  ],
  [
    "name": "description",
    "value":
  ],
  [
    "name": "accent",
    "value":
  ],
  [
    "name": "tags",
    "value":
  ],
  [
    "name": "language",
    "value":
  ],
  [
    "name": "model",
    "value":
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/voice-cloning")! as URL,
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
