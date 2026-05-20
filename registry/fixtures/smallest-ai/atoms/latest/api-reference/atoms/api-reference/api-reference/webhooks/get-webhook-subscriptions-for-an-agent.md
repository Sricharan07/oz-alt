> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get webhook subscriptions for an agent

GET https://api.smallest.ai/atoms/v1/agent/{agentId}/webhook-subscriptions

Retrieve webhook subscriptions for a given agent ID

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/get-webhook-subscriptions-for-an-agent

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{agentId}/webhook-subscriptions:
    get:
      operationId: get-webhook-subscriptions-for-an-agent
      summary: Get webhook subscriptions for an agent
      description: Retrieve webhook subscriptions for a given agent ID
      tags:
        - subpackage_webhooks
      parameters:
        - name: agentId
          in: path
          description: The ID of the agent
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Webhooks_getWebhookSubscriptionsForAnAgent_Response_200
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
        '404':
          description: Agent not found
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/GetWebhookSubscriptionsForAnAgentRequestNotFoundError
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
    WebhookSubscriptionEventType:
      type: string
      enum:
        - pre-conversation
        - post-conversation
        - analytics-completed
      description: The type of event subscribed to
      title: WebhookSubscriptionEventType
    WebhookSubscription:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the subscription
        webhookId:
          type: string
          description: The ID of the webhook
        agentId:
          type: string
          description: The ID of the agent
        eventType:
          $ref: '#/components/schemas/WebhookSubscriptionEventType'
          description: The type of event subscribed to
        createdAt:
          type: string
          format: date-time
          description: The date and time when the subscription was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the subscription was last updated
      title: WebhookSubscription
    Webhooks_getWebhookSubscriptionsForAnAgent_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: array
          items:
            $ref: '#/components/schemas/WebhookSubscription'
      title: Webhooks_getWebhookSubscriptionsForAnAgent_Response_200
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
    GetWebhookSubscriptionsForAnAgentRequestNotFoundError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: GetWebhookSubscriptionsForAnAgentRequestNotFoundError
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
    await client.atoms.agents.getWebhookSubscriptionsForAnAgent("agentId");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.get_webhook_subscriptions_for_an_agent(
    agent_id="agentId",
)

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions"

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

url = URI("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/agentId/webhook-subscriptions")! as URL,
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
