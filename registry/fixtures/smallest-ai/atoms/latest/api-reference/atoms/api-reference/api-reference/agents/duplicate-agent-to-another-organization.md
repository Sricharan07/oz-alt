> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Duplicate agent to another organization

POST https://api.smallest.ai/atoms/v1/agent/{id}/duplicate
Content-Type: application/json

Duplicates a SINGLE_PROMPT agent's live active version into a target organization
(can also be the same organization). Copies all versioned configuration but strips
organization-specific resources: knowledge base tools are removed, default variable
values are blanked, and a new avatar is generated. The duplicate starts with a
published V1 as its active version.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/duplicate-agent-to-another-organization

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/duplicate:
    post:
      operationId: duplicate-agent-to-another-organization
      summary: Duplicate agent to another organization
      description: >
        Duplicates a SINGLE_PROMPT agent's live active version into a target
        organization

        (can also be the same organization). Copies all versioned configuration
        but strips

        organization-specific resources: knowledge base tools are removed,
        default variable

        values are blanked, and a new avatar is generated. The duplicate starts
        with a

        published V1 as its active version.
      tags:
        - subpackage_agents
      parameters:
        - name: id
          in: path
          description: The ID of the source agent to duplicate
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
        '201':
          description: Agent duplicated successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agents_duplicateAgentToAnotherOrganization_Response_201
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
        '403':
          description: Forbidden access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'
        '404':
          description: Not found — source agent or target organization does not exist
          content:
            application/json:
              schema:
                description: Any type
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternalServerErrorResponse'
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                targetOrganizationId:
                  type: string
                  description: >-
                    The ID of the organization to duplicate the agent into. User
                    must be a member of this organization.
              required:
                - targetOrganizationId
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AgentIdDuplicatePostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        _id:
          type: string
          description: The ID of the newly created agent
      title: AgentIdDuplicatePostResponsesContentApplicationJsonSchemaData
    Agents_duplicateAgentToAnotherOrganization_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AgentIdDuplicatePostResponsesContentApplicationJsonSchemaData
      title: Agents_duplicateAgentToAnotherOrganization_Response_201
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

url = "https://api.smallest.ai/atoms/v1/agent/id/duplicate"

payload = { "targetOrganizationId": "5f8d04b2a1c4e72b9c8e4d12" }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/id/duplicate';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"targetOrganizationId":"5f8d04b2a1c4e72b9c8e4d12"}'
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

	url := "https://api.smallest.ai/atoms/v1/agent/id/duplicate"

	payload := strings.NewReader("{\n  \"targetOrganizationId\": \"5f8d04b2a1c4e72b9c8e4d12\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/id/duplicate")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"targetOrganizationId\": \"5f8d04b2a1c4e72b9c8e4d12\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/agent/id/duplicate")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"targetOrganizationId\": \"5f8d04b2a1c4e72b9c8e4d12\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/agent/id/duplicate', [
  'body' => '{
  "targetOrganizationId": "5f8d04b2a1c4e72b9c8e4d12"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/id/duplicate");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"targetOrganizationId\": \"5f8d04b2a1c4e72b9c8e4d12\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["targetOrganizationId": "5f8d04b2a1c4e72b9c8e4d12"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/id/duplicate")! as URL,
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
