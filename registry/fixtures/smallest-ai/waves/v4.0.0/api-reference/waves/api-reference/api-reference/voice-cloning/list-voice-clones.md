> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# List Voice Clones

GET https://api.smallest.ai/waves/v1/voice-cloning

Retrieve all voice clones in your organization.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/voice-cloning/list-voice-clones

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/voice-cloning:
    get:
      operationId: list-voice-clones
      summary: List Voice Clones
      description: |
        Retrieve all voice clones in your organization.
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
          description: List of voice clones.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Voice
                  Cloning_listVoiceClones_Response_200
        '401':
          description: Unauthorized.
          content:
            application/json:
              schema:
                description: Any type
        '500':
          description: Server error.
          content:
            application/json:
              schema:
                description: Any type
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsStatus:
      type: string
      enum:
        - pending
        - processing
        - completed
        - failed
      title: >-
        WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsStatus
    WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsCloningType:
      type: string
      enum:
        - instant
        - professional
      title: >-
        WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsCloningType
    WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItems:
      type: object
      properties:
        _id:
          type: string
        voiceId:
          type: string
        displayName:
          type: string
        description:
          type: string
        accent:
          type: string
        tags:
          type: array
          items:
            type: string
        language:
          type: string
        status:
          $ref: >-
            #/components/schemas/WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsStatus
        cloningType:
          $ref: >-
            #/components/schemas/WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItemsCloningType
        modelIds:
          type: array
          items:
            type: string
          description: |
            Models this clone is compatible with. `lightning-v3.1`
            is the current default. Older entries may list
            `lightning-large`.
        createdAt:
          type: string
          format: date-time
      title: WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItems
    Voice Cloning_listVoiceClones_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItems
      title: Voice Cloning_listVoiceClones_Response_200
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

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.get(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/voice-cloning';
const options = {
  method: 'GET',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{}'
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

	url := "https://api.smallest.ai/waves/v1/voice-cloning"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("GET", url, payload)

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

url = URI("https://api.smallest.ai/waves/v1/voice-cloning")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/waves/v1/voice-cloning")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/waves/v1/voice-cloning', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/voice-cloning");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/voice-cloning")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
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
