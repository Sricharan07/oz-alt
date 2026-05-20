> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Rename a draft

PATCH https://api.smallest.ai/atoms/v1/agent/{id}/drafts/{draftId}
Content-Type: application/json

Rename a draft. For config changes, use PATCH /agent/{id}/drafts/{draftId}/config instead.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-versioning-drafts/rename-a-draft

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/drafts/{draftId}:
    patch:
      operationId: rename-a-draft
      summary: Rename a draft
      description: >
        Rename a draft. For config changes, use PATCH
        /agent/{id}/drafts/{draftId}/config instead.
      tags:
        - subpackage_agentVersioningDrafts
      parameters:
        - name: id
          in: path
          description: The agent ID
          required: true
          schema:
            type: string
        - name: draftId
          in: path
          description: The draft ID
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
          description: Draft renamed successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agent Versioning -
                  Drafts_renameADraft_Response_200
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
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                draftName:
                  type: string
                  description: New name for the draft
              required:
                - draftName
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AgentIdDraftsDraftIdPatchResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        draftName:
          type: string
      title: AgentIdDraftsDraftIdPatchResponsesContentApplicationJsonSchemaData
    Agent Versioning - Drafts_renameADraft_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AgentIdDraftsDraftIdPatchResponsesContentApplicationJsonSchemaData
      title: Agent Versioning - Drafts_renameADraft_Response_200
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

url = "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId"

payload = { "draftName": "Q2 Product Update Draft" }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId';
const options = {
  method: 'PATCH',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"draftName":"Q2 Product Update Draft"}'
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

	url := "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId"

	payload := strings.NewReader("{\n  \"draftName\": \"Q2 Product Update Draft\"\n}")

	req, _ := http.NewRequest("PATCH", url, payload)

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

url = URI("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"draftName\": \"Q2 Product Update Draft\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"draftName\": \"Q2 Product Update Draft\"\n}")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId', [
  'body' => '{
  "draftName": "Q2 Product Update Draft"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"draftName\": \"Q2 Product Update Draft\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["draftName": "Q2 Product Update Draft"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
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
