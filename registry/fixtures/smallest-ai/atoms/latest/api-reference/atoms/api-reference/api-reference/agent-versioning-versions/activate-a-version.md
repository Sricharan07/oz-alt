> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Activate a version

PATCH https://api.smallest.ai/atoms/v1/agent/{id}/versions/{versionId}/activate

Set a published version as the active version for the agent. The previously
active version is deactivated. This does not modify the version's config — it
only changes which version serves live traffic.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-versioning-versions/activate-a-version

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/versions/{versionId}/activate:
    patch:
      operationId: activate-a-version
      summary: Activate a version
      description: >
        Set a published version as the active version for the agent. The
        previously

        active version is deactivated. This does not modify the version's config
        — it

        only changes which version serves live traffic.
      tags:
        - subpackage_agentVersioningVersions
      parameters:
        - name: id
          in: path
          description: The agent ID
          required: true
          schema:
            type: string
        - name: versionId
          in: path
          description: The published version ID
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
          description: Version activated successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agent Versioning -
                  Versions_activateAVersion_Response_200
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
    AgentVersionStatus:
      type: string
      enum:
        - published
        - draft
        - archived
      description: Current status of the version record
      title: AgentVersionStatus
    AgentVersionBlocks:
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
      title: AgentVersionBlocks
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    AgentVersion:
      type: object
      properties:
        _id:
          type: string
          description: Unique identifier
        agent:
          type: string
          description: The agent this version belongs to
        status:
          $ref: '#/components/schemas/AgentVersionStatus'
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
          $ref: '#/components/schemas/AgentVersionBlocks'
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
      description: >-
        Represents either a draft revision or a published version of an agent's
        configuration.
      title: AgentVersion
    Agent Versioning - Versions_activateAVersion_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/AgentVersion'
      title: Agent Versioning - Versions_activateAVersion_Response_200
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

```python
import requests

url = "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate"

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate';
const options = {
  method: 'PATCH',
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

	url := "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate"

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

url = URI("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate")

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

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate");
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/versions/versionId/activate")! as URL,
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
