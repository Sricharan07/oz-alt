> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Text to Speech

POST https://api.smallest.ai/waves/v1/lightning-v2/get_speech
Content-Type: application/json

Get speech for given text using the Waves API

Reference: https://docs.smallest.ai/waves/v-3-0-1/api-reference/api-reference/lightning-v-2/synthesize-lightning-v-2

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves
  version: 1.0.0
paths:
  /waves/v1/lightning-v2/get_speech:
    post:
      operationId: synthesize-lightning-v-2
      summary: Text to Speech
      description: Get speech for given text using the Waves API
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
                  #/components/schemas/Synthesize_lightning_v2RequestBadRequestError
        '401':
          description: Unauthorized.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Synthesize_lightning_v2RequestUnauthorizedError
        '500':
          description: Server error occurred.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Synthesize_lightning_v2RequestInternalServerError
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Lightningv2Request'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    Lightningv2RequestLanguage:
      type: string
      enum:
        - en
        - hi
        - ta
        - kn
        - mr
        - bn
        - gu
        - ar
        - he
        - fr
        - de
        - pl
        - ru
        - it
        - nl
        - es
        - sv
        - ml
        - te
      default: en
      description: >-
        Determines how numbers are spelled out. If set to 'en', numbers will be
        read as individual digits in English. If set to 'hi', numbers will be
        read as individual digits in Hindi.
      title: Lightningv2RequestLanguage
    Lightningv2RequestOutputFormat:
      type: string
      enum:
        - pcm
        - mp3
        - wav
        - ulaw
        - alaw
      default: pcm
      description: The format of the output audio.
      title: Lightningv2RequestOutputFormat
    Lightningv2Request:
      type: object
      properties:
        text:
          type: string
          default: Hey i am your a text to speech model
          description: The text to convert to speech.
        voice_id:
          type: string
          default: malcom
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
          $ref: '#/components/schemas/Lightningv2RequestLanguage'
          default: en
          description: >-
            Determines how numbers are spelled out. If set to 'en', numbers will
            be read as individual digits in English. If set to 'hi', numbers
            will be read as individual digits in Hindi.
        output_format:
          $ref: '#/components/schemas/Lightningv2RequestOutputFormat'
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
      title: Lightningv2Request
    Synthesize_lightning_v2RequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_lightning_v2RequestBadRequestError
    Synthesize_lightning_v2RequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_lightning_v2RequestUnauthorizedError
    Synthesize_lightning_v2RequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type.
        message:
          type: string
          description: Error message.
      title: Synthesize_lightning_v2RequestInternalServerError
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-v2/get_speech"

payload = {
    "text": "Hey i am your a text to speech model",
    "voice_id": "malcom"
}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-v2/get_speech';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"text":"Hey i am your a text to speech model","voice_id":"malcom"}'
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

	url := "https://api.smallest.ai/waves/v1/lightning-v2/get_speech"

	payload := strings.NewReader("{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"malcom\"\n}")

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

url = URI("https://api.smallest.ai/waves/v1/lightning-v2/get_speech")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"malcom\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/lightning-v2/get_speech")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"malcom\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/waves/v1/lightning-v2/get_speech', [
  'body' => '{
  "text": "Hey i am your a text to speech model",
  "voice_id": "malcom"
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

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-v2/get_speech");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"text\": \"Hey i am your a text to speech model\",\n  \"voice_id\": \"malcom\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "text": "Hey i am your a text to speech model",
  "voice_id": "malcom"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-v2/get_speech")! as URL,
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
