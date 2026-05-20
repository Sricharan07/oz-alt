> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create webhook subscriptions for an agent

POST https://api.smallest.ai/atoms/v1/agent/{agentId}/webhook-subscriptions
Content-Type: application/json

Create webhook subscriptions for a specific agent with selected event types

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/create-webhook-subscriptions-for-an-agent

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{agentId}/webhook-subscriptions:
    post:
      operationId: create-webhook-subscriptions-for-an-agent
      summary: Create webhook subscriptions for an agent
      description: >-
        Create webhook subscriptions for a specific agent with selected event
        types
      tags:
        - subpackage_webhooks
      parameters:
        - name: agentId
          in: path
          description: The ID of the agent to create subscriptions for
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
          description: Subscriptions created successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Webhooks_createWebhookSubscriptionsForAnAgent_Response_201
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/CreateWebhookSubscriptionsForAnAgentRequestBadRequestError
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '404':
          description: Agent not found
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/CreateWebhookSubscriptionsForAnAgentRequestNotFoundError
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
                eventTypes:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/AgentAgentIdWebhookSubscriptionsPostRequestBodyContentApplicationJsonSchemaEventTypesItems
                  description: Array of event types to subscribe to
                webhookId:
                  type: string
                  description: The ID of the webhook to subscribe to
              required:
                - eventTypes
                - webhookId
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AgentAgentIdWebhookSubscriptionsPostRequestBodyContentApplicationJsonSchemaEventTypesItems:
      type: string
      enum:
        - pre-conversation
        - post-conversation
        - analytics-completed
      description: The type of event to subscribe to
      title: >-
        AgentAgentIdWebhookSubscriptionsPostRequestBodyContentApplicationJsonSchemaEventTypesItems
    Webhooks_createWebhookSubscriptionsForAnAgent_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: string
          description: Success message
      title: Webhooks_createWebhookSubscriptionsForAnAgent_Response_201
    CreateWebhookSubscriptionsForAnAgentRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: CreateWebhookSubscriptionsForAnAgentRequestBadRequestError
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
    CreateWebhookSubscriptionsForAnAgentRequestNotFoundError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: CreateWebhookSubscriptionsForAnAgentRequestNotFoundError
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
    await client.atoms.agents.createWebhookSubscriptionsForAnAgent("agentId", {
        eventTypes: [
            "pre-conversation",
        ],
        webhookId: "60d0fe4f5311236168a109ca",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.create_webhook_subscriptions_for_an_agent(
    agent_id="agentId",
    event_types=[
        "pre-conversation"
    ],
    webhook_id="60d0fe4f5311236168a109ca",
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

	url := "https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions"

	payload := strings.NewReader("{\n  \"eventTypes\": [\n    \"pre-conversation\"\n  ],\n  \"webhookId\": \"60d0fe4f5311236168a109ca\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"eventTypes\": [\n    \"pre-conversation\"\n  ],\n  \"webhookId\": \"60d0fe4f5311236168a109ca\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"eventTypes\": [\n    \"pre-conversation\"\n  ],\n  \"webhookId\": \"60d0fe4f5311236168a109ca\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions', [
  'body' => '{
  "eventTypes": [
    "pre-conversation"
  ],
  "webhookId": "60d0fe4f5311236168a109ca"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"eventTypes\": [\n    \"pre-conversation\"\n  ],\n  \"webhookId\": \"60d0fe4f5311236168a109ca\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "eventTypes": ["pre-conversation"],
  "webhookId": "60d0fe4f5311236168a109ca"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")! as URL,
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
