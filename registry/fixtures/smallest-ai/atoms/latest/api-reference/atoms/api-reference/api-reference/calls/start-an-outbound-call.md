> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Start an outbound call

POST https://api.smallest.ai/atoms/v1/conversation/outbound
Content-Type: application/json

Initiates an outbound conversation with a specified agent and phone number.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/calls/start-an-outbound-call

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /conversation/outbound:
    post:
      operationId: start-an-outbound-call
      summary: Start an outbound call
      description: >-
        Initiates an outbound conversation with a specified agent and phone
        number.
      tags:
        - subpackage_calls
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
          description: Successfully started the outbound conversation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Calls_startAnOutboundCall_Response_200'
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
                agentId:
                  type: string
                  description: The ID of the agent initiating the conversation
                phoneNumber:
                  type: string
                  description: The phone number to call
                variables:
                  $ref: >-
                    #/components/schemas/ConversationOutboundPostRequestBodyContentApplicationJsonSchemaVariables
                  description: The variables to pass to the conversation
                fromProductId:
                  type: string
                  description: >-
                    The ID of the product to use for the call (get this from the
                    /product/phone-numbers endpoint)
              required:
                - agentId
                - phoneNumber
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    ConversationOutboundPostRequestBodyContentApplicationJsonSchemaVariables:
      type: object
      properties: {}
      description: The variables to pass to the conversation
      title: ConversationOutboundPostRequestBodyContentApplicationJsonSchemaVariables
    ConversationOutboundPostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        conversationId:
          type: string
          description: The ID of the initiated call
      title: ConversationOutboundPostResponsesContentApplicationJsonSchemaData
    Calls_startAnOutboundCall_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/ConversationOutboundPostResponsesContentApplicationJsonSchemaData
      title: Calls_startAnOutboundCall_Response_200
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
    await client.atoms.calls.startAnOutboundCall({
        agentId: "60d0fe4f5311236168a109ca",
        phoneNumber: "+1234567890",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.calls.start_an_outbound_call(
    agent_id="60d0fe4f5311236168a109ca",
    phone_number="+1234567890",
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

	url := "https://api.smallest.ai/atoms/v1/conversation/outbound"

	payload := strings.NewReader("{\n  \"agentId\": \"60d0fe4f5311236168a109ca\",\n  \"phoneNumber\": \"+1234567890\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/conversation/outbound")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"agentId\": \"60d0fe4f5311236168a109ca\",\n  \"phoneNumber\": \"+1234567890\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/conversation/outbound")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"agentId\": \"60d0fe4f5311236168a109ca\",\n  \"phoneNumber\": \"+1234567890\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/conversation/outbound', [
  'body' => '{
  "agentId": "60d0fe4f5311236168a109ca",
  "phoneNumber": "+1234567890"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/conversation/outbound");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"agentId\": \"60d0fe4f5311236168a109ca\",\n  \"phoneNumber\": \"+1234567890\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "agentId": "60d0fe4f5311236168a109ca",
  "phoneNumber": "+1234567890"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/conversation/outbound")! as URL,
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
