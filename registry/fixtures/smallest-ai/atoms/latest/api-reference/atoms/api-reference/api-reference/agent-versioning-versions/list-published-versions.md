> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# List published versions

GET https://api.smallest.ai/atoms/v1/agent/{id}/versions

List published versions for an agent with pagination and optional pin filter.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-versioning-versions/list-published-versions

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/versions:
    get:
      operationId: list-published-versions
      summary: List published versions
      description: >-
        List published versions for an agent with pagination and optional pin
        filter.
      tags:
        - subpackage_agentVersioningVersions
      parameters:
        - name: id
          in: path
          description: The agent ID
          required: true
          schema:
            type: string
        - name: limit
          in: query
          description: Number of versions to return (1-100, default 20)
          required: false
          schema:
            type: integer
            default: 20
        - name: skip
          in: query
          description: Number of versions to skip (default 0)
          required: false
          schema:
            type: integer
            default: 0
        - name: isPinned
          in: query
          description: Filter by pinned status
          required: false
          schema:
            type: boolean
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
                  #/components/schemas/Agent Versioning -
                  Versions_listPublishedVersions_Response_200
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
    AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsStatus:
      type: string
      enum:
        - published
        - draft
        - archived
      description: Current status of the version record
      title: >-
        AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsStatus
    AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsBlocks:
      type: object
      properties:
        workflow_prompt:
          type: string
        workflow_tools:
          type: string
        workflow_graph:
          type: string
        llm:
          type: string
        voice:
          type: string
        language:
          type: string
        call_handling:
          type: string
        detection:
          type: string
        analytics:
          type: string
        timeouts:
          type: string
        audio:
          type: string
        privacy:
          type: string
        widget:
          type: string
      description: References to the 13 config section blocks
      title: >-
        AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsBlocks
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItems:
      type: object
      properties:
        _id:
          type: string
          description: Unique identifier
        agent:
          type: string
          description: The agent this version belongs to
        status:
          $ref: >-
            #/components/schemas/AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsStatus
          description: Current status of the version record
        versionNumber:
          type:
            - integer
            - 'null'
          description: Auto-incremented version number (published versions only)
        label:
          type:
            - string
            - 'null'
          description: Human-readable label for the version
        description:
          type:
            - string
            - 'null'
          description: Description of what changed in this version
        isPinned:
          type: boolean
          default: false
          description: Whether the version is pinned for quick access
        publishedBy:
          type:
            - string
            - 'null'
          description: User ID of who published this version
        draftId:
          type:
            - string
            - 'null'
          description: Unique draft identifier (drafts only)
        draftName:
          type:
            - string
            - 'null'
          description: Human-readable draft name
        draftRevision:
          type:
            - integer
            - 'null'
          description: Revision number within the draft (drafts only)
        sourceVersionId:
          type:
            - string
            - 'null'
          description: The published version this draft was branched from
        blocks:
          $ref: >-
            #/components/schemas/AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItemsBlocks
          description: References to the 13 config section blocks
        workflowType:
          $ref: '#/components/schemas/WorkflowType'
        parentVersion:
          type:
            - string
            - 'null'
          description: The version this was derived from
        isActive:
          type: boolean
          description: Whether this is the currently active version for the agent
        createdBy:
          type: string
          description: User ID of who created this record
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
        publishedByName:
          type:
            - string
            - 'null'
          description: Display name of the user who published
      description: >-
        Represents either a draft revision or a published version of an agent's
        configuration.
      title: AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItems
    AgentIdVersionsGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        versions:
          type: array
          items:
            $ref: >-
              #/components/schemas/AgentIdVersionsGetResponsesContentApplicationJsonSchemaDataVersionsItems
        total:
          type: integer
          description: Total count of matching versions
      title: AgentIdVersionsGetResponsesContentApplicationJsonSchemaData
    Agent Versioning - Versions_listPublishedVersions_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AgentIdVersionsGetResponsesContentApplicationJsonSchemaData
      title: Agent Versioning - Versions_listPublishedVersions_Response_200
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

```python
import requests

url = "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions"

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.get(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions';
const options = {
  method: 'GET',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
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

	url := "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions"

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

url = URI("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions");
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions")! as URL,
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
