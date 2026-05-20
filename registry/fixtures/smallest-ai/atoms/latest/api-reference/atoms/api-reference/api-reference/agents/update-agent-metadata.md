> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Update agent metadata

PATCH https://api.smallest.ai/atoms/v1/agent/{id}
Content-Type: application/json

Update non-versioned agent-level fields: name, description, telephony product, and inbound call settings.

Agent configuration (voice, language, prompt, tools, post-call analytics, etc.) is managed through the
versioning system. Submitting any config-level field here returns 400 with
`"Agent has versioning enabled. Config changes must be made through drafts."`
Use `PATCH /agent/{id}/drafts/{draftId}/config` instead.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/update-agent-metadata

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}:
    patch:
      operationId: update-agent-metadata
      summary: Update agent metadata
      description: >
        Update non-versioned agent-level fields: name, description, telephony
        product, and inbound call settings.

        Agent configuration (voice, language, prompt, tools, post-call
        analytics, etc.) is managed through the

        versioning system. Submitting any config-level field here returns 400
        with

        `"Agent has versioning enabled. Config changes must be made through
        drafts."`

        Use `PATCH /agent/{id}/drafts/{draftId}/config` instead.
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
          description: Agent updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agents_updateAgentMetadata_Response_200'
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
              $ref: '#/components/schemas/UpdateAgentRequest'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    UpdateAgentRequest:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        telephonyProductId:
          type: string
          description: >-
            Telephony product ID to associate with the agent for
            outbound/inbound calls.
        allowInboundCall:
          type: boolean
          description: Whether the agent can receive inbound calls.
      description: >
        Agent metadata update payload. Accepted fields on `PATCH /agent/{id}`

        when versioning is enabled. Any config-level field (language,
        synthesizer,

        slmModel, prompt, tools, post-call analytics, etc.) must be updated
        through

        a draft and published as a new version — see `PATCH
        /agent/{id}/drafts/{draftId}/config`.

        Submitting config fields here returns 400 with

        `"Agent has versioning enabled. Config changes must be made through
        drafts."`.
      title: UpdateAgentRequest
    Agents_updateAgentMetadata_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: string
          description: The ID of the updated agent
      title: Agents_updateAgentMetadata_Response_200
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

```typescript
import { SmallestAIClient } from "smallest-ai";

async function main() {
    const client = new SmallestAIClient({
        token: "YOUR_TOKEN_HERE",
    });
    await client.atoms.agents.updateAnAgent("id", {});
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.update_an_agent(
    id="id",
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

	url := "https://api.smallest.ai/atoms/v1/agent/id"

	payload := strings.NewReader("{}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/agent/id")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/agent/id', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/id");
var request = new RestRequest(Method.PATCH);
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/id")! as URL,
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
