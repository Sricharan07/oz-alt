> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create a campaign

POST https://api.smallest.ai/atoms/v1/campaign
Content-Type: application/json

Create a campaign

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/campaigns/create-a-campaign

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /campaign:
    post:
      operationId: create-a-campaign
      summary: Create a campaign
      description: Create a campaign
      tags:
        - subpackage_campaigns
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
          description: Campaign created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Campaigns_createACampaign_Response_201'
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
                name:
                  type: string
                  description: The name of the campaign
                description:
                  type: string
                  description: The description of the campaign
                audienceId:
                  type: string
                  description: The ID of the audience
                agentId:
                  type: string
                  description: The ID of the agent
                phoneNumberIds:
                  type: array
                  items:
                    type: string
                  description: |
                    Optional list of caller-ID phone number IDs to rotate across
                    when placing outbound calls for this campaign. If omitted,
                    the agent's default phone number is used.
                scheduledAt:
                  type: string
                  format: date-time
                  description: |
                    Optional ISO-8601 timestamp for when the campaign should
                    start dialing. Must be in the future. If provided, the
                    campaign is created in `scheduled` status; otherwise it
                    starts in `draft` status and must be started manually.
                maxRetries:
                  type: integer
                  default: 3
                  description: |
                    Maximum number of times a failed call is retried before the
                    participant is marked as failed. `0` disables retries.
                retryDelay:
                  type: integer
                  default: 15
                  description: |
                    Delay in minutes between retry attempts for a failed call.
              required:
                - name
                - audienceId
                - agentId
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    CampaignPostResponsesContentApplicationJsonSchemaDataStatus:
      type: string
      enum:
        - draft
        - scheduled
        - running
        - paused
        - completed
        - failed
      description: Current campaign status.
      title: CampaignPostResponsesContentApplicationJsonSchemaDataStatus
    CampaignPostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the campaign
        name:
          type: string
          description: The name of the campaign
        description:
          type: string
          description: The description of the campaign
        organization:
          type: string
          description: The ID of the organization
        agentId:
          type: string
          description: The ID of the agent
        createdBy:
          type: string
          description: The ID of the user who created the campaign
        audienceId:
          type: string
          description: The ID of the audience
        participantsCount:
          type: integer
          description: The number of participants in the campaign
        scheduledAt:
          type: string
          format: date-time
          description: The scheduled start time, if provided at creation.
        maxRetries:
          type: integer
          description: Maximum retries per failed call (echoes request).
        retryDelay:
          type: integer
          description: Delay in minutes between retry attempts (echoes request).
        retryAttempts:
          type: integer
          description: Number of retries attempted so far across the campaign.
        status:
          $ref: >-
            #/components/schemas/CampaignPostResponsesContentApplicationJsonSchemaDataStatus
          description: Current campaign status.
        createdAt:
          type: string
          format: date-time
          description: The date and time when the campaign was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the campaign was last updated
      title: CampaignPostResponsesContentApplicationJsonSchemaData
    Campaigns_createACampaign_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/CampaignPostResponsesContentApplicationJsonSchemaData
      title: Campaigns_createACampaign_Response_201
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
    await client.atoms.campaigns.createACampaign({
        name: "My Campaign",
        audienceId: "60d0fe4f5311236168a109ca",
        agentId: "60d0fe4f5311236168a109ca",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.campaigns.create_a_campaign(
    name="My Campaign",
    audience_id="60d0fe4f5311236168a109ca",
    agent_id="60d0fe4f5311236168a109ca",
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

	url := "https://api.smallest.ai/atoms/v1/campaign"

	payload := strings.NewReader("{\n  \"name\": \"My Campaign\",\n  \"audienceId\": \"60d0fe4f5311236168a109ca\",\n  \"agentId\": \"60d0fe4f5311236168a109ca\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/campaign")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"name\": \"My Campaign\",\n  \"audienceId\": \"60d0fe4f5311236168a109ca\",\n  \"agentId\": \"60d0fe4f5311236168a109ca\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/campaign")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"name\": \"My Campaign\",\n  \"audienceId\": \"60d0fe4f5311236168a109ca\",\n  \"agentId\": \"60d0fe4f5311236168a109ca\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/campaign', [
  'body' => '{
  "name": "My Campaign",
  "audienceId": "60d0fe4f5311236168a109ca",
  "agentId": "60d0fe4f5311236168a109ca"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/campaign");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"name\": \"My Campaign\",\n  \"audienceId\": \"60d0fe4f5311236168a109ca\",\n  \"agentId\": \"60d0fe4f5311236168a109ca\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "name": "My Campaign",
  "audienceId": "60d0fe4f5311236168a109ca",
  "agentId": "60d0fe4f5311236168a109ca"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/campaign")! as URL,
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
