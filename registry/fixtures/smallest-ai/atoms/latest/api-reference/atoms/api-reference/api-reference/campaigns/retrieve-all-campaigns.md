> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Retrieve all campaigns

GET https://api.smallest.ai/atoms/v1/campaign
Content-Type: application/json

Get all campaigns

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/campaigns/retrieve-all-campaigns

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /campaign:
    get:
      operationId: retrieve-all-campaigns
      summary: Retrieve all campaigns
      description: Get all campaigns
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
        '200':
          description: A list of campaigns
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Campaigns_retrieveAllCampaigns_Response_200
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
                page:
                  type: number
                  format: double
                  default: 1
                  description: The page number
                limit:
                  type: number
                  format: double
                  default: 10
                  description: The number of items per page
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    CampaignGetResponsesContentApplicationJsonSchemaDataCampaignsItems:
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
        createdAt:
          type: string
          format: date-time
          description: The date and time when the campaign was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the campaign was last updated
        isCampaignInProgress:
          type: boolean
          description: Whether the campaign is in progress
        isCampaignCompleted:
          type: boolean
          description: Whether the campaign is completed
      title: CampaignGetResponsesContentApplicationJsonSchemaDataCampaignsItems
    CampaignGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        campaigns:
          type: array
          items:
            $ref: >-
              #/components/schemas/CampaignGetResponsesContentApplicationJsonSchemaDataCampaignsItems
      title: CampaignGetResponsesContentApplicationJsonSchemaData
    Campaigns_retrieveAllCampaigns_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/CampaignGetResponsesContentApplicationJsonSchemaData
      title: Campaigns_retrieveAllCampaigns_Response_200
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
    await client.atoms.campaigns.retrieveAllCampaigns();
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.campaigns.retrieve_all_campaigns()

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

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("GET", url, payload)

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

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/campaign")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/campaign', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/campaign");
var request = new RestRequest(Method.GET);
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/campaign")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
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
