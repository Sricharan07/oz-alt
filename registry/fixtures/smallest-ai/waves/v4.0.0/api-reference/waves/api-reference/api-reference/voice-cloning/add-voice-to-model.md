> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Add Voice (Deprecated)

POST https://api.smallest.ai/waves/v1/lightning-large/add_voice
Content-Type: multipart/form-data

**Deprecated** — use `POST /waves/v1/voice-cloning` instead. The new
endpoint defaults to `lightning-v3.1`, supports optional metadata,
and returns pre-generated sample clips. This endpoint only clones
onto `lightning-large` and the resulting voices do not work on
`lightning-v3.1` (returns an empty WAV). Kept live for backward
compatibility; new integrations should migrate.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/voice-cloning/add-voice-to-model

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/lightning-large/add_voice:
    post:
      operationId: add-voice-to-model
      summary: Add your Voice (Deprecated)
      description: |
        **Deprecated** — use `POST /waves/v1/voice-cloning` instead. The new
        endpoint defaults to `lightning-v3.1`, supports optional metadata,
        and returns pre-generated sample clips. This endpoint only clones
        onto `lightning-large` and the resulting voices do not work on
        `lightning-v3.1` (returns an empty WAV). Kept live for backward
        compatibility; new integrations should migrate.
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
          description: Voice clone created successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Voice
                  Cloning_addVoiceToModel_Response_200
        '400':
          description: Bad request or limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AddVoiceToModelRequestBadRequestError'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AddVoiceToModelRequestUnauthorizedError'
        '500':
          description: Server error occurred
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AddVoiceToModelRequestInternalServerError'
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                displayName:
                  type: string
                  description: Display name for the voice clone.
                file:
                  type: string
                  format: binary
                  description: Audio file to create voice clone from.
              required:
                - displayName
                - file
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1LightningLargeAddVoicePostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        voiceId:
          type: string
          description: Unique Voice ID.
        model:
          type: string
          description: Model used to generate the voice.
        status:
          type: string
          description: Status of the voice creation.
      required:
        - voiceId
        - model
        - status
      title: >-
        WavesV1LightningLargeAddVoicePostResponsesContentApplicationJsonSchemaData
    Voice Cloning_addVoiceToModel_Response_200:
      type: object
      properties:
        message:
          type: string
          description: Message if the voice clone was created successfully.
        data:
          $ref: >-
            #/components/schemas/WavesV1LightningLargeAddVoicePostResponsesContentApplicationJsonSchemaData
      title: Voice Cloning_addVoiceToModel_Response_200
    AddVoiceToModelRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: AddVoiceToModelRequestBadRequestError
    AddVoiceToModelRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: AddVoiceToModelRequestUnauthorizedError
    AddVoiceToModelRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: AddVoiceToModelRequestInternalServerError
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-large/add_voice"

files = { "file": "open('string', 'rb')" }
payload = { "displayName": "string" }
headers = {"Authorization": "Bearer "}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-large/add_voice';
const form = new FormData();
form.append('displayName', 'string');
form.append('file', 'string');

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

	url := "https://api.smallest.ai/waves/v1/lightning-large/add_voice"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nstring\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"string\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")

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

url = URI("https://api.smallest.ai/waves/v1/lightning-large/add_voice")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nstring\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"string\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/lightning-large/add_voice")
  .header("Authorization", "Bearer ")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nstring\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"string\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/waves/v1/lightning-large/add_voice', [
  'multipart' => [
    [
        'name' => 'displayName',
        'contents' => 'string'
    ],
    [
        'name' => 'file',
        'filename' => 'string',
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

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-large/add_voice");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\nstring\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"string\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]
let parameters = [
  [
    "name": "displayName",
    "value": "string"
  ],
  [
    "name": "file",
    "fileName": "string"
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-large/add_voice")! as URL,
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
