> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Search conversation logs by call IDs

POST https://api.smallest.ai/atoms/v1/conversation/search
Content-Type: application/json

Fetch specific conversation logs by their callIds. This endpoint allows you to retrieve up to 100 specific calls at once.
Only returns calls that belong to agents in your organization (security check enforced).
Unlike the GET /conversation endpoint, this endpoint can also return retry calls (non-root calls).

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/logs/search-conversation-logs-by-call-i-ds

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /conversation/search:
    post:
      operationId: search-conversation-logs-by-call-i-ds
      summary: Search conversation logs by call IDs
      description: >
        Fetch specific conversation logs by their callIds. This endpoint allows
        you to retrieve up to 100 specific calls at once.

        Only returns calls that belong to agents in your organization (security
        check enforced).

        Unlike the GET /conversation endpoint, this endpoint can also return
        retry calls (non-root calls).
      tags:
        - subpackage_logs
      parameters:
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Logs_searchConversationLogsByCallIDs_Response_200
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
                callIds:
                  type: array
                  items:
                    type: string
                  description: Array of callIds to fetch
              required:
                - callIds
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    ConversationSearchPostResponsesContentApplicationJsonSchemaDataLogsItems:
      type: object
      properties: {}
      description: Call log details (same structure as GET /conversation)
      title: ConversationSearchPostResponsesContentApplicationJsonSchemaDataLogsItems
    ConversationSearchPostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        logs:
          type: array
          items:
            $ref: >-
              #/components/schemas/ConversationSearchPostResponsesContentApplicationJsonSchemaDataLogsItems
        total:
          type: integer
          description: Number of logs returned
        requestedCount:
          type: integer
          description: Number of callIds requested
      title: ConversationSearchPostResponsesContentApplicationJsonSchemaData
    Logs_searchConversationLogsByCallIDs_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/ConversationSearchPostResponsesContentApplicationJsonSchemaData
      title: Logs_searchConversationLogsByCallIDs_Response_200
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

```typescript
import { SmallestAIClient } from "smallest-ai";

async function main() {
    const client = new SmallestAIClient({
        token: "YOUR_TOKEN_HERE",
    });
    await client.atoms.logs.searchConversationLogsByCallIDs({
        callIds: [
            "CALL-1737000000000-abc123",
            "CALL-1737000000001-def456",
        ],
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.logs.search_conversation_logs_by_call_i_ds(
    call_ids=[
        "CALL-1737000000000-abc123",
        "CALL-1737000000001-def456"
    ],
)

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

	url := "https://api.smallest.ai/atoms/v1/conversation/search"

	payload := strings.NewReader("{\n  \"callIds\": [\n    \"CALL-1737000000000-abc123\",\n    \"CALL-1737000000001-def456\"\n  ]\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/conversation/search")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"callIds\": [\n    \"CALL-1737000000000-abc123\",\n    \"CALL-1737000000001-def456\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/conversation/search")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"callIds\": [\n    \"CALL-1737000000000-abc123\",\n    \"CALL-1737000000001-def456\"\n  ]\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/conversation/search', [
  'body' => '{
  "callIds": [
    "CALL-1737000000000-abc123",
    "CALL-1737000000001-def456"
  ]
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/conversation/search");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"callIds\": [\n    \"CALL-1737000000000-abc123\",\n    \"CALL-1737000000001-def456\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["callIds": ["CALL-1737000000000-abc123", "CALL-1737000000001-def456"]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/conversation/search")! as URL,
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
