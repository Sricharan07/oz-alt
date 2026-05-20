> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get agent workflow

GET https://api.smallest.ai/atoms/v1/agent/{id}/workflow

**Deprecated** — prefer `GET /agent/{id}` (config is resolved into `_resolvedConfig`
including prompt, tools, and post-call analytics).

Returns the active version's prompt and tools for single-prompt agents, or the
workflow graph data for workflow_graph agents. Customers still rely on this to
fetch their current prompt + tools — endpoint is kept live for now.

**Caveat:** the `versionId` query param (if passed) is silently ignored.
The response always reflects the currently-active version. To inspect a
non-active version, use `GET /agent/{id}/versions/{versionId}`.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/get-agent-workflow

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/workflow:
    get:
      operationId: get-agent-workflow
      summary: Get agent workflow
      description: >
        **Deprecated** — prefer `GET /agent/{id}` (config is resolved into
        `_resolvedConfig`

        including prompt, tools, and post-call analytics).

        Returns the active version's prompt and tools for single-prompt agents,
        or the

        workflow graph data for workflow_graph agents. Customers still rely on
        this to

        fetch their current prompt + tools — endpoint is kept live for now.

        **Caveat:** the `versionId` query param (if passed) is silently ignored.

        The response always reflects the currently-active version. To inspect a

        non-active version, use `GET /agent/{id}/versions/{versionId}`.
      tags:
        - subpackage_agents
      parameters:
        - name: id
          in: path
          description: The ID of the agent
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agents_getAgentWorkflow_Response_200'
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '404':
          description: Agent not found
          content:
            application/json:
              schema:
                description: Any type
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
    ToolType:
      type: string
      enum:
        - end_call
        - transfer_call
        - api_call
        - extract_dynamic_variables
        - knowledge_base_search
      description: The type of function/tool
      title: ToolType
    ToolTransferOptionType:
      type: string
      enum:
        - cold_transfer
        - warm_transfer
      default: cold_transfer
      description: >-
        Transfer mode. `cold_transfer` hands off immediately; `warm_transfer`
        briefs the receiving party first.
      title: ToolTransferOptionType
    ToolTransferOptionPrivateHandoffOptionType:
      type: string
      enum:
        - prompt
        - static
      description: '`prompt` generates briefing from the LLM; `static` plays fixed text.'
      title: ToolTransferOptionPrivateHandoffOptionType
    ToolTransferOptionPrivateHandoffOption:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/ToolTransferOptionPrivateHandoffOptionType'
          description: '`prompt` generates briefing from the LLM; `static` plays fixed text.'
        prompt:
          type: string
          description: The prompt or static text for the private handoff.
      description: >-
        Private briefing delivered to the transfer target before the caller is
        connected. Only used when `type = warm_transfer`.
      title: ToolTransferOptionPrivateHandoffOption
    ToolTransferOptionPublicHandoffOptionType:
      type: string
      enum:
        - prompt
        - static
      title: ToolTransferOptionPublicHandoffOptionType
    ToolTransferOptionPublicHandoffOption:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/ToolTransferOptionPublicHandoffOptionType'
        prompt:
          type: string
      description: >-
        Message played to the caller while the transfer is being set up. Only
        used when `type = warm_transfer`.
      title: ToolTransferOptionPublicHandoffOption
    ToolTransferOption:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/ToolTransferOptionType'
          default: cold_transfer
          description: >-
            Transfer mode. `cold_transfer` hands off immediately;
            `warm_transfer` briefs the receiving party first.
        privateHandoffOption:
          oneOf:
            - $ref: '#/components/schemas/ToolTransferOptionPrivateHandoffOption'
            - type: 'null'
          description: >-
            Private briefing delivered to the transfer target before the caller
            is connected. Only used when `type = warm_transfer`.
        publicHandoffOption:
          oneOf:
            - $ref: '#/components/schemas/ToolTransferOptionPublicHandoffOption'
            - type: 'null'
          description: >-
            Message played to the caller while the transfer is being set up.
            Only used when `type = warm_transfer`.
      description: >-
        Required for transfer_call type. Controls cold vs warm transfer
        behavior.
      title: ToolTransferOption
    ToolOnHoldMusic:
      type: string
      enum:
        - ringtone
        - relaxing_sound
        - uplifting_beats
        - none
      default: ringtone
      description: >-
        Optional for transfer_call type. Audio played to the caller while the
        transfer is in progress.
      title: ToolOnHoldMusic
    ToolMethod:
      type: string
      enum:
        - GET
        - POST
        - PUT
        - DELETE
        - PATCH
      description: Required for api_call type. HTTP method to use.
      title: ToolMethod
    ToolHeadersArrayItems:
      type: object
      properties:
        key:
          type: string
        value:
          type: string
      required:
        - key
        - value
      title: ToolHeadersArrayItems
    ToolQueryParamsItems:
      type: object
      properties:
        key:
          type: string
        value:
          type: string
      required:
        - key
        - value
      title: ToolQueryParamsItems
    ToolLlmParametersItemsType:
      type: string
      enum:
        - text
        - number
        - boolean
        - enum
      title: ToolLlmParametersItemsType
    ToolLlmParametersItems:
      type: object
      properties:
        name:
          type: string
          description: Parameter name
        description:
          type: string
          description: What the parameter represents
        type:
          $ref: '#/components/schemas/ToolLlmParametersItemsType'
        values:
          type: array
          items:
            type: string
          description: Required when type is `enum`. Allowed values.
        required:
          type: boolean
          default: false
      required:
        - name
        - description
        - type
      title: ToolLlmParametersItems
    ToolResponseVariablesItems:
      type: object
      properties:
        variableName:
          type: string
          description: Name to store the extracted value under
        jsonPath:
          type: string
          description: JSON path to extract the value from the response
      required:
        - variableName
        - jsonPath
      title: ToolResponseVariablesItems
    ToolVariablesExtractionSchemaItemsType:
      type: string
      enum:
        - text
        - number
        - boolean
        - enum
      title: ToolVariablesExtractionSchemaItemsType
    ToolVariablesExtractionSchemaItems:
      type: object
      properties:
        name:
          type: string
          description: Name of the variable to extract
        description:
          type: string
          description: What this variable represents
        type:
          $ref: '#/components/schemas/ToolVariablesExtractionSchemaItemsType'
        values:
          type: array
          items:
            type: string
          description: Required when type is `enum`. List of possible values.
      required:
        - name
        - description
        - type
      title: ToolVariablesExtractionSchemaItems
    Tool:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/ToolType'
          description: The type of function/tool
        name:
          type: string
          description: Unique name for the function (no spaces)
        description:
          type: string
          description: Description of what the function does
        enabled:
          type: boolean
          default: true
          description: Whether the tool is enabled
        transferNumber:
          type: string
          description: >-
            Required for transfer_call type. Phone number to transfer the call
            to (E.164 format)
        transferOption:
          $ref: '#/components/schemas/ToolTransferOption'
          description: >-
            Required for transfer_call type. Controls cold vs warm transfer
            behavior.
        onHoldMusic:
          $ref: '#/components/schemas/ToolOnHoldMusic'
          default: ringtone
          description: >-
            Optional for transfer_call type. Audio played to the caller while
            the transfer is in progress.
        transferOnlyIfHuman:
          type: boolean
          default: true
          description: >-
            Optional for transfer_call type. If true, the call is only
            transferred when a human is detected on the receiving end
            (voicemail/IVR skipped).
        detectionTimeout:
          type: integer
          default: 30
          description: >-
            Optional for transfer_call type. Seconds to wait for human detection
            before giving up (5–60).
        url:
          type: string
          format: uri
          description: Required for api_call type. The URL to make the HTTP request to.
        method:
          $ref: '#/components/schemas/ToolMethod'
          description: Required for api_call type. HTTP method to use.
        timeout:
          type: integer
          default: 5000
          description: >-
            Optional for api_call type. Request timeout in milliseconds
            (1000–30000).
        headers:
          type: object
          additionalProperties:
            type: string
          description: Optional for api_call type. Static HTTP headers as a key/value map.
        headersArray:
          type: array
          items:
            $ref: '#/components/schemas/ToolHeadersArrayItems'
          description: >-
            Optional for api_call type. Headers as an array of key/value objects
            (alternative to `headers` map).
        queryParams:
          type: array
          items:
            $ref: '#/components/schemas/ToolQueryParamsItems'
          description: >-
            Optional for api_call type. Query parameters to include in the
            request URL. Values support variable templating like `{{order_id}}`.
        requestBody:
          type: string
          description: >-
            Optional for api_call type. Raw request body as a JSON string.
            Supports variable templating.
        llmParameters:
          type: array
          items:
            $ref: '#/components/schemas/ToolLlmParametersItems'
          description: >-
            Optional for api_call type. Parameters the LLM can supply
            dynamically at runtime.
        responseVariables:
          type: array
          items:
            $ref: '#/components/schemas/ToolResponseVariablesItems'
          default: []
          description: >-
            Optional for api_call type. Variables to extract from the API
            response into the agent's variable store.
        variablesExtractionSchema:
          type: array
          items:
            $ref: '#/components/schemas/ToolVariablesExtractionSchemaItems'
          description: >-
            Required for extract_dynamic_variables type. Schema defining
            variables to extract from the conversation.
        knowledgeBaseId:
          type: string
          description: >-
            Required for knowledge_base_search type. ID of the knowledge base to
            search.
        fillerPhrases:
          type: array
          items:
            type: string
          default: []
          description: >-
            Optional for knowledge_base_search type. Phrases spoken while
            searching.
      required:
        - type
        - name
        - description
      description: >
        Tool (function) available to the agent. The `type` field determines
        which

        additional fields are required. Backend validation enforces per-type
        schemas.
      title: Tool
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    WorkflowGraphDataNodesItemsPosition:
      type: object
      properties:
        x:
          type: number
          format: double
        'y':
          type: number
          format: double
      title: WorkflowGraphDataNodesItemsPosition
    WorkflowGraphDataNodesItemsData:
      type: object
      properties: {}
      description: Node-specific data and configuration
      title: WorkflowGraphDataNodesItemsData
    WorkflowGraphDataNodesItems:
      type: object
      properties:
        id:
          type: string
          description: Unique identifier for the node
        type:
          type: string
          description: Type of the node (e.g., default_node, end_call, pre_call_api)
        position:
          $ref: '#/components/schemas/WorkflowGraphDataNodesItemsPosition'
        data:
          $ref: '#/components/schemas/WorkflowGraphDataNodesItemsData'
          description: Node-specific data and configuration
      title: WorkflowGraphDataNodesItems
    WorkflowGraphDataEdgesItems:
      type: object
      properties:
        id:
          type: string
          description: Unique identifier for the edge
        source:
          type: string
          description: ID of the source node
        target:
          type: string
          description: ID of the target node
        type:
          type: string
          description: Type of the edge
      title: WorkflowGraphDataEdgesItems
    WorkflowGraphData:
      type: object
      properties:
        nodes:
          type: array
          items:
            $ref: '#/components/schemas/WorkflowGraphDataNodesItems'
          description: Array of workflow nodes
        edges:
          type: array
          items:
            $ref: '#/components/schemas/WorkflowGraphDataEdgesItems'
          description: Array of workflow edges connecting nodes
      description: Workflow configuration using a node-based graph structure
      title: WorkflowGraphData
    SinglePromptDataToolsItems:
      type: object
      properties: {}
      description: Tool configuration object
      title: SinglePromptDataToolsItems
    SinglePromptData:
      type: object
      properties:
        prompt:
          type: string
          description: The main prompt that defines the agent's behavior and responses
        tools:
          type: array
          items:
            $ref: '#/components/schemas/SinglePromptDataToolsItems'
          description: Array of tools/functions available to the agent
      description: Workflow configuration using a simple prompt-based approach
      title: SinglePromptData
    AgentIdWorkflowGetResponsesContentApplicationJsonSchemaDataData:
      oneOf:
        - $ref: '#/components/schemas/WorkflowGraphData'
        - $ref: '#/components/schemas/SinglePromptData'
      description: Graph data for workflow_graph agents.
      title: AgentIdWorkflowGetResponsesContentApplicationJsonSchemaDataData
    AgentIdWorkflowGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        prompt:
          type: string
          description: Active prompt (single-prompt agents only).
        tools:
          type: array
          items:
            $ref: '#/components/schemas/Tool'
          description: Active tool list (single-prompt agents only).
        type:
          $ref: '#/components/schemas/WorkflowType'
          description: Workflow type. Present for workflow_graph agents.
        data:
          $ref: >-
            #/components/schemas/AgentIdWorkflowGetResponsesContentApplicationJsonSchemaDataData
          description: Graph data for workflow_graph agents.
      description: The active version's workflow.
      title: AgentIdWorkflowGetResponsesContentApplicationJsonSchemaData
    Agents_getAgentWorkflow_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AgentIdWorkflowGetResponsesContentApplicationJsonSchemaData
          description: The active version's workflow.
      title: Agents_getAgentWorkflow_Response_200
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
    await client.atoms.agents.getAgentWorkflow("id");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.get_agent_workflow(
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

	url := "https://api.smallest.ai/atoms/v1/agent/id/workflow"

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

url = URI("https://api.smallest.ai/atoms/v1/agent/id/workflow")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/agent/id/workflow")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/agent/id/workflow', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/id/workflow");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/id/workflow")! as URL,
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
