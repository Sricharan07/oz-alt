> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get a campaign

GET https://api.smallest.ai/atoms/v1/campaign/{id}

Get a campaign with detailed metrics

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/campaigns/get-a-campaign

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /campaign/{id}:
    get:
      operationId: get-a-campaign
      summary: Get a campaign
      description: Get a campaign with detailed metrics
      tags:
        - subpackage_campaigns
      parameters:
        - name: id
          in: path
          description: The ID of the campaign
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
          description: Campaign details with metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Campaigns_getACampaign_Response_200'
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
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaignStatus:
      type: string
      enum:
        - draft
        - scheduled
        - running
        - paused
        - scheduled_for_retry
        - completed
      description: The current status of the campaign
      title: CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaignStatus
    CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaign:
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
        status:
          $ref: >-
            #/components/schemas/CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaignStatus
          description: The current status of the campaign
        maxRetries:
          type: integer
          description: Maximum number of retry attempts
        retryDelay:
          type: integer
          description: Delay between retries in minutes
        scheduledAt:
          type: string
          format: date-time
          description: Scheduled start time for the campaign
        createdAt:
          type: string
          format: date-time
          description: The date and time when the campaign was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the campaign was last updated
      title: CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaign
    CampaignIdGetResponsesContentApplicationJsonSchemaDataEventsItems:
      type: object
      properties:
        _id:
          type: string
        campaignId:
          type: string
        triggerSource:
          type: string
        eventAction:
          type: string
        createdAt:
          type: string
          format: date-time
      title: CampaignIdGetResponsesContentApplicationJsonSchemaDataEventsItems
    CampaignIdGetResponsesContentApplicationJsonSchemaDataMetrics:
      type: object
      properties:
        total_participants:
          type: integer
          description: Total number of contacts in the campaign audience
        contacts_called:
          type: integer
          description: >-
            Number of unique contacts where call was attempted (statuses
            IN_PROGRESS, COMPLETED, FAILED, NO_ANSWER)
        contacts_connected:
          type: integer
          description: >-
            Number of unique contacts who answered and had a conversation
            (status COMPLETED)
      description: Campaign performance metrics
      title: CampaignIdGetResponsesContentApplicationJsonSchemaDataMetrics
    CampaignIdGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        campaign:
          $ref: >-
            #/components/schemas/CampaignIdGetResponsesContentApplicationJsonSchemaDataCampaign
        events:
          type: array
          items:
            $ref: >-
              #/components/schemas/CampaignIdGetResponsesContentApplicationJsonSchemaDataEventsItems
          description: Campaign events history
        metrics:
          $ref: >-
            #/components/schemas/CampaignIdGetResponsesContentApplicationJsonSchemaDataMetrics
          description: Campaign performance metrics
      title: CampaignIdGetResponsesContentApplicationJsonSchemaData
    Campaigns_getACampaign_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/CampaignIdGetResponsesContentApplicationJsonSchemaData
      title: Campaigns_getACampaign_Response_200
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
    await client.atoms.campaigns.getACampaign("id");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.campaigns.get_a_campaign(
    id="id",
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

	url := "https://api.smallest.ai/atoms/v1/campaign/id"

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

url = URI("https://api.smallest.ai/atoms/v1/campaign/id")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/campaign/id")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/campaign/id', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/campaign/id");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/campaign/id")! as URL,
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
