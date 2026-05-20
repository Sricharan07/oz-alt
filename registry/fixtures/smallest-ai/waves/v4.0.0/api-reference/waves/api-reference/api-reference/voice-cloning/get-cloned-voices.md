> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get Cloned Voices (Deprecated)

GET https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices

**Deprecated** — use `GET /waves/v1/voice-cloning` instead. The new
list endpoint returns the same data plus a `modelIds` array per
clone. Kept live for backward compatibility.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/voice-cloning/get-cloned-voices

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/lightning-large/get_cloned_voices:
    get:
      operationId: get-cloned-voices
      summary: Get your cloned Voices (Deprecated)
      description: |
        **Deprecated** — use `GET /waves/v1/voice-cloning` instead. The new
        list endpoint returns the same data plus a `modelIds` array per
        clone. Kept live for backward compatibility.
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
          description: Voices retrieved successfully.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Voice
                  Cloning_getClonedVoices_Response_200
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetClonedVoicesRequestBadRequestError'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetClonedVoicesRequestUnauthorizedError'
        '500':
          description: Server error occurred
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetClonedVoicesRequestInternalServerError'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1LightningLargeGetClonedVoicesGetResponsesContentApplicationJsonSchemaVoicesItems:
      type: object
      properties:
        displayName:
          type: string
          description: Display name for the voice.
        accent:
          type: string
          description: Accent of the voice.
        tags:
          type: array
          items:
            type: string
          description: List of tags associated with the voice.
        voiceId:
          type: string
          description: Unique Voice ID.
        model:
          type: string
          description: Model used to generate the voice.
        status:
          type: string
          description: Status of the voice generation.
        createdAt:
          type: string
          format: date-time
          description: Date and time the voice was created.
      required:
        - displayName
        - voiceId
      title: >-
        WavesV1LightningLargeGetClonedVoicesGetResponsesContentApplicationJsonSchemaVoicesItems
    Voice Cloning_getClonedVoices_Response_200:
      type: object
      properties:
        voices:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1LightningLargeGetClonedVoicesGetResponsesContentApplicationJsonSchemaVoicesItems
          description: List of available voices.
      title: Voice Cloning_getClonedVoices_Response_200
    GetClonedVoicesRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: GetClonedVoicesRequestBadRequestError
    GetClonedVoicesRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: GetClonedVoicesRequestUnauthorizedError
    GetClonedVoicesRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: GetClonedVoicesRequestInternalServerError
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices"

headers = {"Authorization": "Bearer "}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices';
const options = {method: 'GET', headers: {Authorization: 'Bearer '}};

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
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices"

	req, _ := http.NewRequest("GET", url, nil)

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

url = URI("https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-large/get_cloned_voices")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
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
