> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Delete an agent

DELETE https://api.smallest.ai/atoms/v1/agent/{id}/archive

Delete an agent. The agent is removed from listings and stops accepting calls.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/delete-agent

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/archive:
    delete:
      operationId: delete-agent
      summary: Delete an agent
      description: >-
        Delete an agent. The agent is removed from listings and stops accepting
        calls.
      tags:
        - subpackage_agents
      parameters:
        - name: id
          in: path
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
          description: Agent deleted successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agents_deleteAgent_Response_200'
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
        '401':
          description: Access token is missing or invalid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'
        '403':
          description: Forbidden access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    Agents_deleteAgent_Response_200:
      type: object
      properties:
        status:
          type: boolean
      title: Agents_deleteAgent_Response_200
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
    ApiResponseData:
      type: object
      properties: {}
      title: ApiResponseData
    ApiResponse:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/ApiResponseData'
      title: ApiResponse
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

url = "https://api.smallest.ai/atoms/v1/agent/id/archive"

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.delete(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/id/archive';
const options = {
  method: 'DELETE',
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

	url := "https://api.smallest.ai/atoms/v1/agent/id/archive"

	payload := strings.NewReader("{}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/id/archive")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.delete("https://api.smallest.ai/atoms/v1/agent/id/archive")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('DELETE', 'https://api.smallest.ai/atoms/v1/agent/id/archive', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/id/archive");
var request = new RestRequest(Method.DELETE);
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/id/archive")! as URL,
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
