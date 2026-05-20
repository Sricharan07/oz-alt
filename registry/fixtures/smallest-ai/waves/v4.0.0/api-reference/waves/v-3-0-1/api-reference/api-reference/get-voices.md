> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get Voices

GET https://api.smallest.ai/waves/v1/{model}/get_voices

Get voices supported for a given model using the new Waves API.

Reference: https://docs.smallest.ai/waves/v-3-0-1/api-reference/api-reference/get-voices

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves
  version: 1.0.0
paths:
  /waves/v1/{model}/get_voices:
    get:
      operationId: get-voices
      summary: Get Voices
      description: Get voices supported for a given model using the new Waves API.
      tags:
        - ''
      parameters:
        - name: model
          in: path
          description: The model to use for speech synthesis.
          required: true
          schema:
            $ref: '#/components/schemas/WavesV1ModelGetVoicesGetParametersModel'
        - name: Authorization
          in: header
          description: Bearer authentication
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Voices retrieved successfully.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/get_voices_Response_200'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Get_voicesRequestBadRequestError'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Get_voicesRequestUnauthorizedError'
        '500':
          description: Server error occurred
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Get_voicesRequestInternalServerError'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    WavesV1ModelGetVoicesGetParametersModel:
      type: string
      enum:
        - lightning
        - lightning-large
        - lightning-v2
        - lightning-v3.1
      default: lightning-v3.1
      title: WavesV1ModelGetVoicesGetParametersModel
    WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItemsTags:
      type: object
      properties:
        language:
          type: array
          items:
            type: string
          description: Language of the voice.
        accent:
          type: string
          description: Accent of the voice.
        gender:
          type: string
          description: Gender of the voice.
      description: List of tags associated with the voice.
      title: >-
        WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItemsTags
    WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItems:
      type: object
      properties:
        voiceId:
          type: string
          description: Unique Voice ID.
        displayName:
          type: string
          description: Display name for the voice.
        tags:
          $ref: >-
            #/components/schemas/WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItemsTags
          description: List of tags associated with the voice.
      required:
        - voiceId
        - displayName
      title: WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItems
    get_voices_Response_200:
      type: object
      properties:
        voices:
          type: array
          items:
            $ref: >-
              #/components/schemas/WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItems
          description: List of available voices.
      title: get_voices_Response_200
    Get_voicesRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: Get_voicesRequestBadRequestError
    Get_voicesRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: Get_voicesRequestUnauthorizedError
    Get_voicesRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: Get_voicesRequestInternalServerError
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

headers = {"Authorization": "Bearer "}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices';
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

	url := "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

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

url = URI("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")! as URL,
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
