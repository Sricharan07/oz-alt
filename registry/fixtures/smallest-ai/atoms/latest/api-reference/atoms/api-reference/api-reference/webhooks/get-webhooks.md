> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get webhooks

GET https://api.smallest.ai/atoms/v1/webhook

Retrieve all webhooks for the organization or a specific webhook by ID

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/get-webhooks

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /webhook:
    get:
      operationId: get-webhooks
      summary: Get webhooks
      description: Retrieve all webhooks for the organization or a specific webhook by ID
      tags:
        - subpackage_webhooks
      parameters:
        - name: webhookId
          in: query
          required: false
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
                $ref: '#/components/schemas/Webhooks_getWebhooks_Response_200'
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
    WebhookStatus:
      type: string
      enum:
        - enabled
        - disabled
      description: The status of the webhook
      title: WebhookStatus
    WebhookAgent:
      type: object
      properties:
        _id:
          type: string
          description: The ID of the agent
        name:
          type: string
          description: The name of the agent
        description:
          type: string
          description: The description of the agent
      title: WebhookAgent
    WebhookSubscriptionPopulatedEventType:
      type: string
      enum:
        - pre-conversation
        - post-conversation
        - analytics-completed
      description: The type of event subscribed to
      title: WebhookSubscriptionPopulatedEventType
    WebhookSubscriptionPopulated:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the subscription
        webhookId:
          type: string
          description: The ID of the webhook
        agentId:
          oneOf:
            - $ref: '#/components/schemas/WebhookAgent'
            - type: 'null'
          description: The populated agent details, or null if not assigned
        eventType:
          $ref: '#/components/schemas/WebhookSubscriptionPopulatedEventType'
          description: The type of event subscribed to
        createdAt:
          type: string
          format: date-time
          description: The date and time when the subscription was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the subscription was last updated
      title: WebhookSubscriptionPopulated
    Webhook:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the webhook
        url:
          type: string
          description: The webhook endpoint URL
        description:
          type: string
          description: The description of the webhook
        status:
          $ref: '#/components/schemas/WebhookStatus'
          description: The status of the webhook
        organizationId:
          type: string
          description: The organization ID
        createdBy:
          type: string
          description: The user ID who created the webhook
        subscriptions:
          type: array
          items:
            $ref: '#/components/schemas/WebhookSubscriptionPopulated'
          description: >-
            A list of subscriptions for the webhook with populated agent
            details.
        decryptedSecretKey:
          type: string
          description: >-
            The decrypted signing secret for the webhook. This is only returned
            when fetching a single webhook by ID.
        createdAt:
          type: string
          format: date-time
          description: The date and time when the webhook was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the webhook was last updated
      title: Webhook
    WebhookGetResponsesContentApplicationJsonSchemaData1:
      type: array
      items:
        $ref: '#/components/schemas/Webhook'
      title: WebhookGetResponsesContentApplicationJsonSchemaData1
    WebhookGetResponsesContentApplicationJsonSchemaData:
      oneOf:
        - $ref: '#/components/schemas/Webhook'
        - $ref: >-
            #/components/schemas/WebhookGetResponsesContentApplicationJsonSchemaData1
      title: WebhookGetResponsesContentApplicationJsonSchemaData
    Webhooks_getWebhooks_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/WebhookGetResponsesContentApplicationJsonSchemaData
      title: Webhooks_getWebhooks_Response_200
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
    await client.atoms.webhooks.getWebhooks({});
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.webhooks.get_webhooks()

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/webhook"

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

url = URI("https://api.smallest.ai/atoms/v1/webhook")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/webhook")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/webhook', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/webhook");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/webhook")! as URL,
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
