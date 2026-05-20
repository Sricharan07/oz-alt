> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get all conversation logs

GET https://api.smallest.ai/atoms/v1/conversation

Retrieve paginated conversation logs with support for various filters. Returns call logs for agents belonging to the authenticated user's organization.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/logs/get-all-conversation-logs

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /conversation:
    get:
      operationId: get-all-conversation-logs
      summary: Get all conversation logs
      description: >-
        Retrieve paginated conversation logs with support for various filters.
        Returns call logs for agents belonging to the authenticated user's
        organization.
      tags:
        - subpackage_logs
      parameters:
        - name: page
          in: query
          description: Page number for pagination
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            default: 5
        - name: agentIds
          in: query
          description: Comma-separated list of agent IDs to filter by
          required: false
          schema:
            type: string
        - name: campaignIds
          in: query
          description: Comma-separated list of campaign IDs to filter by
          required: false
          schema:
            type: string
        - name: callTypes
          in: query
          description: Comma-separated list of call types to filter by
          required: false
          schema:
            $ref: '#/components/schemas/ConversationGetParametersCallTypes'
        - name: search
          in: query
          description: Search query to filter by callId, fromNumber, or toNumber
          required: false
          schema:
            type: string
        - name: statusFilter
          in: query
          description: >
            Comma-separated list of call statuses to filter by.

            Available statuses: pending, in_progress, completed, failed,
            no_answer, cancelled, busy
          required: false
          schema:
            type: string
        - name: disconnectReasonFilter
          in: query
          description: >
            Comma-separated list of disconnect reasons to filter by.

            Available reasons: user_hangup, agent_hangup, connection_error,
            timeout, system_error, transfer_complete
          required: false
          schema:
            type: string
        - name: callAttemptFilter
          in: query
          description: >
            Comma-separated list of call attempt types to filter by.

            Available filters: initial (first attempt calls), retry (retry
            attempt calls), all (all calls)
          required: false
          schema:
            type: string
        - name: durationFilter
          in: query
          description: >
            Comma-separated list of duration ranges to filter by.

            Available ranges: 0-30 (0-30 seconds), 30-60 (30-60 seconds), 1-5
            (1-5 minutes), 5+ (more than 5 minutes)
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
                $ref: '#/components/schemas/Logs_getAllConversationLogs_Response_200'
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
    ConversationGetParametersCallTypes:
      type: string
      enum:
        - telephony_inbound
        - telephony_outbound
        - chat
      title: ConversationGetParametersCallTypes
    ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsStatus:
      type: string
      enum:
        - pending
        - in_progress
        - completed
        - failed
        - no_answer
        - cancelled
        - busy
      description: The status of the call
      title: ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsStatus
    ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsType:
      type: string
      enum:
        - telephony_inbound
        - telephony_outbound
        - chat
      description: The type of call
      title: ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsType
    ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsAgentDispositionConfigItems:
      type: object
      properties:
        identifier:
          type: string
        type:
          type: string
      title: >-
        ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsAgentDispositionConfigItems
    ConversationGetResponsesContentApplicationJsonSchemaDataLogsItems:
      type: object
      properties:
        _id:
          type: string
          description: The database ID of the call log
        callId:
          type: string
          description: The unique call identifier
        status:
          $ref: >-
            #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsStatus
          description: The status of the call
        duration:
          type: number
          format: double
          description: The duration of the call in seconds
        from:
          type: string
          description: The phone number the call was made from
        to:
          type: string
          description: The phone number the call was made to
        type:
          $ref: >-
            #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsType
          description: The type of call
        agentId:
          type: string
          description: The ID of the agent that handled the call
        agentName:
          type: string
          description: The name of the agent
        recordingUrl:
          type: string
          description: URL to the call recording (if available)
        recordingDualUrl:
          type: string
          description: URL to the dual-channel call recording (if available)
        disconnectionReason:
          type: string
          description: The reason the call was disconnected
        retryCount:
          type: integer
          description: Number of retry attempts for this call
        createdAt:
          type: string
          format: date-time
          description: When the call was created
        dispositionMetrics:
          type: object
          additionalProperties:
            type: string
          description: Custom disposition metrics for the call
        agentDispositionConfig:
          type: array
          items:
            $ref: >-
              #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataLogsItemsAgentDispositionConfigItems
          description: Configuration for disposition metrics
      title: ConversationGetResponsesContentApplicationJsonSchemaDataLogsItems
    ConversationGetResponsesContentApplicationJsonSchemaDataPagination:
      type: object
      properties:
        total:
          type: integer
          description: Total number of matching call logs
        page:
          type: integer
          description: Current page number
        limit:
          type: integer
          description: Number of items per page (page size)
        hasMore:
          type: boolean
          description: Whether there are more pages available
        totalPages:
          type: integer
          description: Total number of pages
      title: ConversationGetResponsesContentApplicationJsonSchemaDataPagination
    ConversationGetResponsesContentApplicationJsonSchemaDataDispositionMetricsConfigItems:
      type: object
      properties:
        identifier:
          type: string
        type:
          type: string
      title: >-
        ConversationGetResponsesContentApplicationJsonSchemaDataDispositionMetricsConfigItems
    ConversationGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        logs:
          type: array
          items:
            $ref: >-
              #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataLogsItems
        pagination:
          $ref: >-
            #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataPagination
        dispositionMetricsConfig:
          type: array
          items:
            $ref: >-
              #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaDataDispositionMetricsConfigItems
          description: Global disposition metrics configuration
      title: ConversationGetResponsesContentApplicationJsonSchemaData
    Logs_getAllConversationLogs_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/ConversationGetResponsesContentApplicationJsonSchemaData
      title: Logs_getAllConversationLogs_Response_200
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
    await client.atoms.logs.getAllConversationLogs({
        page: 1,
        limit: 10,
        agentIds: "60d0fe4f5311236168a109ca,60d0fe4f5311236168a109cb",
        campaignIds: "60d0fe4f5311236168a109ca,60d0fe4f5311236168a109cb",
        callTypes: "telephony_inbound",
        search: "+1234567890",
        statusFilter: "completed,failed",
        disconnectReasonFilter: "user_hangup,agent_hangup",
        callAttemptFilter: "initial",
        durationFilter: "0-30,30-60",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.logs.get_all_conversation_logs(
    page=1,
    limit=10,
    agent_ids="60d0fe4f5311236168a109ca,60d0fe4f5311236168a109cb",
    campaign_ids="60d0fe4f5311236168a109ca,60d0fe4f5311236168a109cb",
    call_types="telephony_inbound",
    search="+1234567890",
    status_filter="completed,failed",
    disconnect_reason_filter="user_hangup,agent_hangup",
    call_attempt_filter="initial",
    duration_filter="0-30,30-60",
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

	url := "https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60"

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

url = URI("https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/conversation?page=1&limit=10&agentIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&campaignIds=60d0fe4f5311236168a109ca%2C60d0fe4f5311236168a109cb&callTypes=telephony_inbound&search=%2B1234567890&statusFilter=completed%2Cfailed&disconnectReasonFilter=user_hangup%2Cagent_hangup&callAttemptFilter=initial&durationFilter=0-30%2C30-60")! as URL,
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
