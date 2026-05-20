> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create a webhook

POST https://api.smallest.ai/atoms/v1/webhook
Content-Type: application/json

Create a new webhook with subscriptions for specific agents and events

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/create-a-webhook

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /webhook:
    post:
      operationId: create-a-webhook
      summary: Create a webhook
      description: Create a new webhook with subscriptions for specific agents and events
      tags:
        - subpackage_webhooks
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
        '201':
          description: Webhook created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhooks_createAWebhook_Response_201'
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
                endpoint:
                  type: string
                  description: The webhook endpoint URL
                description:
                  type: string
                  description: The description of the webhook
                events:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/WebhookPostRequestBodyContentApplicationJsonSchemaEventsItems
                  description: Array of events to subscribe to
              required:
                - endpoint
                - description
                - events
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    WebhookPostRequestBodyContentApplicationJsonSchemaEventsItemsEventType:
      type: string
      enum:
        - pre-conversation
        - post-conversation
        - analytics-completed
      description: The type of event to subscribe to
      title: WebhookPostRequestBodyContentApplicationJsonSchemaEventsItemsEventType
    WebhookPostRequestBodyContentApplicationJsonSchemaEventsItems:
      type: object
      properties:
        agentId:
          type: string
          description: The ID of the agent
        eventType:
          $ref: >-
            #/components/schemas/WebhookPostRequestBodyContentApplicationJsonSchemaEventsItemsEventType
          description: The type of event to subscribe to
      title: WebhookPostRequestBodyContentApplicationJsonSchemaEventsItems
    Webhooks_createAWebhook_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: string
          description: The ID of the created webhook
      title: Webhooks_createAWebhook_Response_201
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
    await client.atoms.webhooks.createAWebhook({
        endpoint: "https://example.com/webhook",
        description: "Webhook for conversation events",
        events: [
            {},
        ],
    });
}
main();

```

```python
from smallest_ai import SmallestAI
from smallest_ai.atoms.webhooks import PostWebhookRequestEventsItem

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.webhooks.create_a_webhook(
    endpoint="https://example.com/webhook",
    description="Webhook for conversation events",
    events=[
        PostWebhookRequestEventsItem()
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

	url := "https://api.smallest.ai/atoms/v1/webhook"

	payload := strings.NewReader("{\n  \"endpoint\": \"https://example.com/webhook\",\n  \"description\": \"Webhook for conversation events\",\n  \"events\": [\n    {}\n  ]\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/webhook")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"endpoint\": \"https://example.com/webhook\",\n  \"description\": \"Webhook for conversation events\",\n  \"events\": [\n    {}\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/webhook")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"endpoint\": \"https://example.com/webhook\",\n  \"description\": \"Webhook for conversation events\",\n  \"events\": [\n    {}\n  ]\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/webhook', [
  'body' => '{
  "endpoint": "https://example.com/webhook",
  "description": "Webhook for conversation events",
  "events": [
    {}
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/webhook");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"endpoint\": \"https://example.com/webhook\",\n  \"description\": \"Webhook for conversation events\",\n  \"events\": [\n    {}\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "endpoint": "https://example.com/webhook",
  "description": "Webhook for conversation events",
  "events": [[]]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/webhook")! as URL,
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
