> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Delete a Voice Clone

DELETE https://api.smallest.ai/waves/v1/lightning-large
Content-Type: application/json

Delete a voice clone by `voiceId`. Despite the `/lightning-large/`
path, this endpoint deletes any voice clone on the organization,
including clones created via `POST /waves/v1/voice-cloning`.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/voice-cloning/delete-voice-clone

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/lightning-large:
    delete:
      operationId: delete-voice-clone
      summary: Delete a Voice Clone
      description: |
        Delete a voice clone by `voiceId`. Despite the `/lightning-large/`
        path, this endpoint deletes any voice clone on the organization,
        including clones created via `POST /waves/v1/voice-cloning`.
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
          description: Voice clone deleted successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Voice
                  Cloning_deleteVoiceClone_Response_200
        '400':
          description: Bad request (Invalid voice ID or validation error)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeleteVoiceCloneRequestBadRequestError'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeleteVoiceCloneRequestUnauthorizedError'
        '500':
          description: Server error occurred
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/DeleteVoiceCloneRequestInternalServerError
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                voiceId:
                  type: string
                  description: The unique identifier of the voice clone to delete.
              required:
                - voiceId
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    Voice Cloning_deleteVoiceClone_Response_200:
      type: object
      properties:
        success:
          type: boolean
          description: Status if the voice clone was deleted successfully.
        voiceId:
          type: string
          description: Voice ID of the deleted voice clone.
      required:
        - voiceId
      title: Voice Cloning_deleteVoiceClone_Response_200
    DeleteVoiceCloneRequestBadRequestError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: DeleteVoiceCloneRequestBadRequestError
    DeleteVoiceCloneRequestUnauthorizedError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: DeleteVoiceCloneRequestUnauthorizedError
    DeleteVoiceCloneRequestInternalServerError:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Error message
      title: DeleteVoiceCloneRequestInternalServerError
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/waves/v1/lightning-large"

payload = { "voiceId": "string" }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.delete(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/lightning-large';
const options = {
  method: 'DELETE',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"voiceId":"string"}'
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

	url := "https://api.smallest.ai/waves/v1/lightning-large"

	payload := strings.NewReader("{\n  \"voiceId\": \"string\"\n}")

	req, _ := http.NewRequest("DELETE", url, payload)

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

url = URI("https://api.smallest.ai/waves/v1/lightning-large")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"voiceId\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.delete("https://api.smallest.ai/waves/v1/lightning-large")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"voiceId\": \"string\"\n}")
  .asString();
```

```php
request('DELETE', 'https://api.smallest.ai/waves/v1/lightning-large', [
  'body' => '{
  "voiceId": "string"
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

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-large");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"voiceId\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["voiceId": "string"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-large")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
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
