> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get agent by ID

GET https://api.smallest.ai/atoms/v1/agent/{id}

Returns the agent document merged with the currently-active version's resolved
config under `_resolvedConfig`. Non-versioned fields (name, telephonyProductId,
allowInboundCall, etc.) sit at the top level; versioned fields (prompt, tools,
language, synthesizer, post-call analytics, …) are resolved from the active
version and exposed under `_resolvedConfig`.

Notable resolved fields:

- `_resolvedConfig.postCallAnalyticsConfig` — disposition metrics + analytics model flags
- `_resolvedConfig.tools` — configured tools on the active version
- `_resolvedConfig.prompt` — active version's prompt
- `activeVersionId` / `versionId` — current published & active version ID

To read prompt + tools alone, use `GET /agent/{id}/workflow` (deprecated for
new integrations but still live). To inspect a specific non-active version,
use `GET /agent/{id}/versions/{versionId}`.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/get-agent-by-id

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}:
    get:
      operationId: get-agent-by-id
      summary: Get agent by ID
      description: >
        Returns the agent document merged with the currently-active version's
        resolved

        config under `_resolvedConfig`. Non-versioned fields (name,
        telephonyProductId,

        allowInboundCall, etc.) sit at the top level; versioned fields (prompt,
        tools,

        language, synthesizer, post-call analytics, …) are resolved from the
        active

        version and exposed under `_resolvedConfig`.

        Notable resolved fields:

        - `_resolvedConfig.postCallAnalyticsConfig` — disposition metrics +
        analytics model flags

        - `_resolvedConfig.tools` — configured tools on the active version

        - `_resolvedConfig.prompt` — active version's prompt

        - `activeVersionId` / `versionId` — current published & active version
        ID

        To read prompt + tools alone, use `GET /agent/{id}/workflow` (deprecated
        for

        new integrations but still live). To inspect a specific non-active
        version,

        use `GET /agent/{id}/versions/{versionId}`.
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agents_getAgentById_Response_200'
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
    AgentDtoBackgroundSound:
      type: string
      enum:
        - ''
        - office
        - cafe
        - call_center
        - static
      description: >-
        Ambient background sound during calls. Options: '' (none), 'office',
        'cafe', 'call_center', 'static'.
      title: AgentDtoBackgroundSound
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    AgentDtoLanguageEnabled:
      type: string
      enum:
        - en
        - hi
        - ta
      description: The language of the agent
      title: AgentDtoLanguageEnabled
    AgentDtoLanguageSwitching:
      type: object
      properties:
        isEnabled:
          type: boolean
          description: Whether language switching is enabled for the agent
        minWordsForDetection:
          type: number
          format: double
          description: Minimum number of words required for language detection
        strongSignalThreshold:
          type: number
          format: double
          description: Threshold for strong language signal detection
        weakSignalThreshold:
          type: number
          format: double
          description: Threshold for weak language signal detection
        minConsecutiveForWeakThresholdSwitch:
          type: number
          format: double
          description: >-
            Minimum consecutive detections required for weak threshold language
            switch
      description: Language switching configuration for the agent
      title: AgentDtoLanguageSwitching
    AgentDtoLanguage:
      type: object
      properties:
        enabled:
          $ref: '#/components/schemas/AgentDtoLanguageEnabled'
          description: The language of the agent
        switching:
          $ref: '#/components/schemas/AgentDtoLanguageSwitching'
          description: Language switching configuration for the agent
        supported:
          type: array
          items:
            type: string
          description: The supported languages of the agent
      description: The language configuration of the agent
      title: AgentDtoLanguage
    AgentDtoSynthesizerVoiceConfigModel:
      type: string
      enum:
        - waves
        - waves_lightning_large
        - waves_lightning_large_voice_clone
      default: waves_lightning_large
      description: The model of the synthesizer
      title: AgentDtoSynthesizerVoiceConfigModel
    AgentDtoSynthesizerVoiceConfigGender:
      type: string
      enum:
        - male
        - female
      default: female
      title: AgentDtoSynthesizerVoiceConfigGender
    AgentDtoSynthesizerVoiceConfig:
      type: object
      properties:
        model:
          $ref: '#/components/schemas/AgentDtoSynthesizerVoiceConfigModel'
          default: waves_lightning_large
          description: The model of the synthesizer
        voiceId:
          type: string
          default: nyah
          description: The voice ID of the synthesizer.
        gender:
          $ref: '#/components/schemas/AgentDtoSynthesizerVoiceConfigGender'
          default: female
      description: The voice configuration of the synthesizer
      title: AgentDtoSynthesizerVoiceConfig
    AgentDtoSynthesizer:
      type: object
      properties:
        voiceConfig:
          $ref: '#/components/schemas/AgentDtoSynthesizerVoiceConfig'
          description: The voice configuration of the synthesizer
        speed:
          type: number
          format: double
          default: 1.2
          description: The speed of the synthesizer
        consistency:
          type: number
          format: double
          default: 0.5
          description: The consistency of the synthesizer
        similarity:
          type: number
          format: double
          default: 0
          description: The similarity of the synthesizer
        enhancement:
          type: number
          format: double
          default: 1
          description: The enhancement of the synthesizer
      description: The synthesizer (TTS) configuration of the agent
      title: AgentDtoSynthesizer
    AgentDtoSlmModel:
      type: string
      enum:
        - electron
        - gpt-4o
      description: >-
        The LLM model to use for the agent. LLM model will be used to generate
        the response and take decisions based on the user's query.
      title: AgentDtoSlmModel
    AgentDtoDefaultVariables:
      type: object
      properties: {}
      description: >-
        The default variables to use for the agent. These variables will be used
        if no variables are provided when initiating a conversation with the
        agent.
      title: AgentDtoDefaultVariables
    AgentDtoPreCallApiMethod:
      type: string
      enum:
        - GET
        - POST
        - PUT
        - DELETE
        - PATCH
      description: The HTTP method to use for the API call.
      title: AgentDtoPreCallApiMethod
    AgentDtoPreCallApiBody:
      type: object
      properties: {}
      description: Optional request body for POST/PUT/PATCH requests.
      title: AgentDtoPreCallApiBody
    AgentDtoPreCallApiQueryParams:
      type: object
      properties: {}
      description: Optional query parameters to include in the request URL.
      title: AgentDtoPreCallApiQueryParams
    AgentDtoPreCallApiResponseVariablesItems:
      type: object
      properties:
        variableName:
          type: string
          description: The name of the variable to inject into the agent prompt.
        jsonPath:
          type: string
          description: JSON path expression to extract the value from the API response.
      required:
        - variableName
        - jsonPath
      title: AgentDtoPreCallApiResponseVariablesItems
    AgentDtoPreCallApi:
      type: object
      properties:
        isEnabled:
          type: boolean
          default: false
          description: Whether the pre-call API is enabled.
        url:
          type: string
          format: uri
          description: The URL of the API endpoint to call.
        method:
          $ref: '#/components/schemas/AgentDtoPreCallApiMethod'
          description: The HTTP method to use for the API call.
        headers:
          type: object
          additionalProperties:
            type: string
          description: Optional HTTP headers to include in the request.
        body:
          $ref: '#/components/schemas/AgentDtoPreCallApiBody'
          description: Optional request body for POST/PUT/PATCH requests.
        timeout:
          type: integer
          default: 5
          description: Timeout in seconds for the API call.
        queryParams:
          $ref: '#/components/schemas/AgentDtoPreCallApiQueryParams'
          description: Optional query parameters to include in the request URL.
        responseVariables:
          type: array
          items:
            $ref: '#/components/schemas/AgentDtoPreCallApiResponseVariablesItems'
          description: >-
            List of variables to extract from the API response using JSON path
            expressions.
      required:
        - url
        - method
      description: >-
        Configuration for an API call to be made before the call starts. The
        response variables can be injected into the agent's prompt.
      title: AgentDtoPreCallApi
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
    DispositionMetricDispositionMetricType:
      type: string
      enum:
        - STRING
        - BOOLEAN
        - INTEGER
        - ENUM
        - DATETIME
      description: Data type returned by the metric.
      title: DispositionMetricDispositionMetricType
    DispositionMetric:
      type: object
      properties:
        identifier:
          type: string
          description: >-
            Stable machine identifier. Lowercase letters, digits, and
            underscores only.
        dispositionMetricPrompt:
          type: string
          description: >-
            Natural-language question evaluated against the transcript after the
            call ends.
        dispositionMetricType:
          $ref: '#/components/schemas/DispositionMetricDispositionMetricType'
          description: Data type returned by the metric.
        choices:
          type: array
          items:
            type: string
          description: Required when `dispositionMetricType = ENUM`. Allowed values.
      required:
        - identifier
        - dispositionMetricPrompt
        - dispositionMetricType
      description: |
        A single disposition metric captured after each call. The metric prompt
        is evaluated against the call transcript post-call, and the result is
        returned in the call log under `postCallAnalytics.dispositionMetrics`.
      title: DispositionMetric
    PostCallAnalyticsConfigSuccessMetricsItemsSuccessMetricType:
      type: string
      enum:
        - NUMERIC_SCALE
        - PERCENTAGE_SCALE
        - PASS_FAIL
        - DESCRIPTIVE_SCALE
      title: PostCallAnalyticsConfigSuccessMetricsItemsSuccessMetricType
    PostCallAnalyticsConfigSuccessMetricsItems:
      type: object
      properties:
        identifier:
          type: string
        successMetricPrompt:
          type: string
        successMetricType:
          $ref: >-
            #/components/schemas/PostCallAnalyticsConfigSuccessMetricsItemsSuccessMetricType
      required:
        - identifier
        - successMetricPrompt
        - successMetricType
      title: PostCallAnalyticsConfigSuccessMetricsItems
    PostCallAnalyticsConfig:
      type: object
      properties:
        dispositionMetrics:
          type: array
          items:
            $ref: '#/components/schemas/DispositionMetric'
          default: []
          description: Structured metrics extracted from each completed call.
        successMetrics:
          type: array
          items:
            $ref: '#/components/schemas/PostCallAnalyticsConfigSuccessMetricsItems'
          default: []
          description: |
            **Deprecated** — will be removed in a future version. Use
            `dispositionMetrics` instead. Kept here because the backend still
            accepts it on writes and returns it on reads.
        summaryPrompt:
          type: string
          default: ''
          description: |
            **Deprecated** — no longer used in post-call analysis and will be
            removed in a future version. Kept here because the backend still
            accepts it on writes and returns it on reads.
        useInternalAnalyticsModel:
          type: boolean
          default: true
          description: >-
            Use the internal analytics model. When false, falls back to the
            agent's own LLM.
        useReasoningModel:
          type: boolean
          default: false
          description: >-
            Route analytics evaluation through the reasoning model for
            higher-quality results at a latency/cost tradeoff.
      description: >
        Per-agent post-call analytics configuration. Evaluated after each call
        ends

        and surfaced in call logs under the `postCallAnalytics` field.
      title: PostCallAnalyticsConfig
    AgentDtoResolvedConfig:
      type: object
      properties:
        prompt:
          type: string
          description: Active version's single-prompt text.
        tools:
          type: array
          items:
            $ref: '#/components/schemas/Tool'
          description: Active version's configured tools.
        postCallAnalyticsConfig:
          $ref: '#/components/schemas/PostCallAnalyticsConfig'
        callDispositionConfig:
          type: string
      description: |
        The active version's config resolved into a flat shape. Populated when
        the agent has a published, activated version.
      title: AgentDtoResolvedConfig
    AgentDTO:
      type: object
      properties:
        _id:
          type: string
          description: The ID of the agent
        name:
          type: string
          description: The name of the agent
        description:
          type: string
          description: The description of the agent
        backgroundSound:
          $ref: '#/components/schemas/AgentDtoBackgroundSound'
          description: >-
            Ambient background sound during calls. Options: '' (none), 'office',
            'cafe', 'call_center', 'static'.
        organization:
          type: string
          description: The organization ID of the agent
        workflowId:
          type: string
          description: The workflow ID of the agent
        workflowType:
          $ref: '#/components/schemas/WorkflowType'
          description: The type of workflow used by the agent
        createdBy:
          type: string
          description: The user ID of the user who created the agent
        globalKnowledgeBaseId:
          type: string
          description: The global knowledge base ID of the agent
        language:
          $ref: '#/components/schemas/AgentDtoLanguage'
          description: The language configuration of the agent
        synthesizer:
          $ref: '#/components/schemas/AgentDtoSynthesizer'
          description: The synthesizer (TTS) configuration of the agent
        slmModel:
          $ref: '#/components/schemas/AgentDtoSlmModel'
          description: >-
            The LLM model to use for the agent. LLM model will be used to
            generate the response and take decisions based on the user's query.
        defaultVariables:
          $ref: '#/components/schemas/AgentDtoDefaultVariables'
          description: >-
            The default variables to use for the agent. These variables will be
            used if no variables are provided when initiating a conversation
            with the agent.
        preCallAPI:
          $ref: '#/components/schemas/AgentDtoPreCallApi'
          description: >-
            Configuration for an API call to be made before the call starts. The
            response variables can be injected into the agent's prompt.
        createdAt:
          type: string
          format: date-time
          description: The date and time when the agent was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the agent was last updated
        activeVersionId:
          type: string
          description: ID of the currently-active published version. Matches `versionId`.
        versionId:
          type: string
          description: Alias for `activeVersionId`.
        _resolvedConfig:
          $ref: '#/components/schemas/AgentDtoResolvedConfig'
          description: >
            The active version's config resolved into a flat shape. Populated
            when

            the agent has a published, activated version.
      title: AgentDTO
    Agents_getAgentById_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/AgentDTO'
      title: Agents_getAgentById_Response_200
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
    await client.atoms.agents.getAgentById("id");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.get_agent_by_id(
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

	url := "https://api.smallest.ai/atoms/v1/agent/id"

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

url = URI("https://api.smallest.ai/atoms/v1/agent/id")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/agent/id")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/agent/id', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/id");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/id")! as URL,
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
