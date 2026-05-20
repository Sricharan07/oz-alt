> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Diff two versions

GET https://api.smallest.ai/atoms/v1/agent/{id}/versions/diff

Compare two published versions side-by-side by their IDs.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-versioning-versions/diff-two-versions

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/versions/diff:
    get:
      operationId: diff-two-versions
      summary: Diff two versions
      description: Compare two published versions side-by-side by their IDs.
      tags:
        - subpackage_agentVersioningVersions
      parameters:
        - name: id
          in: path
          description: The agent ID
          required: true
          schema:
            type: string
        - name: versionA
          in: query
          description: ID of the first version
          required: true
          schema:
            type: string
        - name: versionB
          in: query
          description: ID of the second version
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: >-
            API key from the console ApiKey collection, sent as Bearer token.
            Also accepts session cookies for browser-based auth.
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Diff returned successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agent Versioning -
                  Versions_diffTwoVersions_Response_200
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternalServerErrorResponse'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AgentIdVersionsDiffGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties: {}
      description: Section-by-section diff between the two versions
      title: AgentIdVersionsDiffGetResponsesContentApplicationJsonSchemaData
    Agent Versioning - Versions_diffTwoVersions_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AgentIdVersionsDiffGetResponsesContentApplicationJsonSchemaData
          description: Section-by-section diff between the two versions
      title: Agent Versioning - Versions_diffTwoVersions_Response_200
    BadRequestErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: BadRequestErrorResponse
    UnauthorizedErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: UnauthorizedErrorResponse
    InternalServerErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: InternalServerErrorResponse
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      description: >-
        API key from the console ApiKey collection, sent as Bearer token. Also
        accepts session cookies for browser-based auth.

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff"

querystring = {"versionA":"5f8d0d55b54764421b7156c1","versionB":"5f8d0d55b54764421b7156c2"}

payload = { "id": "60d0fe4f5311236168a109ca" }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.get(url, json=payload, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2';
const options = {
  method: 'GET',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"id":"60d0fe4f5311236168a109ca"}'
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

	url := "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2"

	payload := strings.NewReader("{\n  \"id\": \"60d0fe4f5311236168a109ca\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"id\": \"60d0fe4f5311236168a109ca\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"id\": \"60d0fe4f5311236168a109ca\"\n}")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2', [
  'body' => '{
  "id": "60d0fe4f5311236168a109ca"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"id\": \"60d0fe4f5311236168a109ca\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["id": "60d0fe4f5311236168a109ca"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/diff?versionA=5f8d0d55b54764421b7156c1&versionB=5f8d0d55b54764421b7156c2")! as URL,
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
