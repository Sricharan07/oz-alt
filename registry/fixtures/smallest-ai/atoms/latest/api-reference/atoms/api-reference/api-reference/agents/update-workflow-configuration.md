> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Update workflow configuration

PATCH https://api.smallest.ai/atoms/v1/workflow/{id}
Content-Type: application/json

**Deprecated** — use `PATCH /agent/{id}/drafts/{draftId}/config` instead.

Directly mutates the legacy workflow document for an agent. This write path
bypasses the versioning system entirely: the change is not captured as a
new version, and future version activations may overwrite the legacy doc
back to whatever the version snapshot contains.

⚠ **Writing here on a versioned agent can silently wipe tools, prompt, or
other fields that were missing from the PATCH payload.** Only use this if
you know the agent is not using versioning, or if you are intentionally
hot-patching the legacy doc.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/update-workflow-configuration

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /workflow/{id}:
    patch:
      operationId: update-workflow-configuration
      summary: Update workflow configuration
      description: >
        **Deprecated** — use `PATCH /agent/{id}/drafts/{draftId}/config`
        instead.

        Directly mutates the legacy workflow document for an agent. This write
        path

        bypasses the versioning system entirely: the change is not captured as a

        new version, and future version activations may overwrite the legacy doc

        back to whatever the version snapshot contains.

        ⚠ **Writing here on a versioned agent can silently wipe tools, prompt,
        or

        other fields that were missing from the PATCH payload.** Only use this
        if

        you know the agent is not using versioning, or if you are intentionally

        hot-patching the legacy doc.
      tags:
        - subpackage_agents
      parameters:
        - name: id
          in: path
          description: The workflow ID (found at `agent.workflowId` on the agent document).
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
          description: Workflow updated successfully.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agents_updateWorkflowConfiguration_Response_200
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
        '404':
          description: Workflow not found.
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
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                type:
                  $ref: '#/components/schemas/WorkflowType'
                workflowGraph:
                  $ref: >-
                    #/components/schemas/WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraph
                  description: >-
                    Required when `type = workflow_graph`. Exactly one of
                    `workflowGraph` or `singlePromptConfig` must be provided.
                singlePromptConfig:
                  $ref: '#/components/schemas/SinglePromptConfig'
              required:
                - type
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphNodesItems:
      type: object
      properties: {}
      title: >-
        WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphNodesItems
    WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphEdgesItems:
      type: object
      properties: {}
      title: >-
        WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphEdgesItems
    WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraph:
      type: object
      properties:
        nodes:
          type: array
          items:
            $ref: >-
              #/components/schemas/WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphNodesItems
        edges:
          type: array
          items:
            $ref: >-
              #/components/schemas/WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraphEdgesItems
      description: >-
        Required when `type = workflow_graph`. Exactly one of `workflowGraph` or
        `singlePromptConfig` must be provided.
      title: WorkflowIdPatchRequestBodyContentApplicationJsonSchemaWorkflowGraph
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
    SinglePromptConfig:
      type: object
      properties:
        prompt:
          type: string
          description: The main prompt that defines the agent's behavior and responses
        tools:
          type: array
          items:
            $ref: '#/components/schemas/Tool'
          default: []
          description: >
            Array of tools/functions available to the agent during
            conversations.

            Five tool types are supported: `end_call`, `transfer_call`,
            `api_call`,

            `extract_dynamic_variables`, and `knowledge_base_search`. Each type
            has its

            own required fields — see `Tool` schema.
      required:
        - prompt
      description: Configuration for single prompt workflow type
      title: SinglePromptConfig
    Agents_updateWorkflowConfiguration_Response_200:
      type: object
      properties: {}
      description: Empty response body
      title: Agents_updateWorkflowConfiguration_Response_200
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
    await client.atoms.workflows.updateWorkflowConfiguration("60d0fe4f5311236168a109ca", {
        type: "workflow_graph",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.workflows.update_workflow_configuration(
    id="60d0fe4f5311236168a109ca",
    type="workflow_graph",
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

	url := "https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca"

	payload := strings.NewReader("{\n  \"type\": \"workflow_graph\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"type\": \"workflow_graph\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"type\": \"workflow_graph\"\n}")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca', [
  'body' => '{
  "type": "workflow_graph"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"type\": \"workflow_graph\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["type": "workflow_graph"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/workflow/60d0fe4f5311236168a109ca")! as URL,
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
