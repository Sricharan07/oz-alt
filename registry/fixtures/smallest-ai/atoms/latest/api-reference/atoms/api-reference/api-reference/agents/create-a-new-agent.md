> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create a new agent

POST https://api.smallest.ai/atoms/v1/agent
Content-Type: application/json

You can create a new agent by passing the name of the agent in the request body. You can use update-workflow endpoint next to assign custom workflow to the agent.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/create-a-new-agent

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent:
    post:
      operationId: create-a-new-agent
      summary: Create a new agent
      description: >-
        You can create a new agent by passing the name of the agent in the
        request body. You can use update-workflow endpoint next to assign custom
        workflow to the agent.
      tags:
        - subpackage_agents
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
          description: Agent created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agents_createANewAgent_Response_201'
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
              $ref: '#/components/schemas/CreateAgentRequest'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    CreateAgentRequestBackgroundSound:
      type: string
      enum:
        - ''
        - office
        - cafe
        - call_center
        - static
      default: ''
      description: >-
        Ambient background sound during calls. Options: '' (none), 'office',
        'cafe', 'call_center', 'static'.
      title: CreateAgentRequestBackgroundSound
    CreateAgentRequestLanguageEnabled:
      type: string
      enum:
        - en
        - hi
        - ta
      default: en
      description: >-
        The language of the agent. Supported: 'en' (English), 'hi' (Hindi), 'ta'
        (Tamil).
      title: CreateAgentRequestLanguageEnabled
    CreateAgentRequestLanguageSwitching:
      type: object
      properties:
        isEnabled:
          type: boolean
          default: false
          description: Whether to enable language switching for the agent
        minWordsForDetection:
          type: number
          format: double
          default: 2
          description: Minimum number of words required for language detection
        strongSignalThreshold:
          type: number
          format: double
          default: 0.7
          description: Threshold for strong language signal detection (0.1 to 0.9)
        weakSignalThreshold:
          type: number
          format: double
          default: 0.3
          description: Threshold for weak language signal detection (0.1 to 0.9)
        minConsecutiveForWeakThresholdSwitch:
          type: number
          format: double
          default: 2
          description: >-
            Minimum consecutive detections required for weak threshold language
            switch
      description: >-
        Language switching configuration for the agent. If enabled, the agent
        will be able to switch between languages based on the user's language.
      title: CreateAgentRequestLanguageSwitching
    CreateAgentRequestLanguage:
      type: object
      properties:
        enabled:
          $ref: '#/components/schemas/CreateAgentRequestLanguageEnabled'
          default: en
          description: >-
            The language of the agent. Supported: 'en' (English), 'hi' (Hindi),
            'ta' (Tamil).
        switching:
          $ref: '#/components/schemas/CreateAgentRequestLanguageSwitching'
          description: >-
            Language switching configuration for the agent. If enabled, the
            agent will be able to switch between languages based on the user's
            language.
      description: >-
        Language configuration for the agent. You can enable or disable language
        switching for the agent. This will be used to determine the language of
        the agent.
      title: CreateAgentRequestLanguage
    CreateAgentRequestSynthesizerVoiceConfigOneOf0Model:
      type: string
      enum:
        - waves_lightning_large_voice_clone
      description: >-
        We currently support 3 types of models for the synthesizer. Waves, Waves
        Lightning Large and Waves Lightning Large Voice Clone. You can clone
        your voice using waves platform and use the voiceId for this field and
        select the model as waves_lightning_large_voice_clone to use your cloned
        voice.
      title: CreateAgentRequestSynthesizerVoiceConfigOneOf0Model
    CreateAgentRequestSynthesizerVoiceConfigOneOf0Gender:
      type: string
      enum:
        - male
        - female
      description: >-
        The gender of the synthesizer. When selecting gender, you have to select
        the model and voiceId which are required fields.
      title: CreateAgentRequestSynthesizerVoiceConfigOneOf0Gender
    CreateAgentRequestSynthesizerVoiceConfig0:
      type: object
      properties:
        model:
          $ref: >-
            #/components/schemas/CreateAgentRequestSynthesizerVoiceConfigOneOf0Model
          description: >-
            We currently support 3 types of models for the synthesizer. Waves,
            Waves Lightning Large and Waves Lightning Large Voice Clone. You can
            clone your voice using waves platform and use the voiceId for this
            field and select the model as waves_lightning_large_voice_clone to
            use your cloned voice.
        voiceId:
          type: string
        gender:
          $ref: >-
            #/components/schemas/CreateAgentRequestSynthesizerVoiceConfigOneOf0Gender
          description: >-
            The gender of the synthesizer. When selecting gender, you have to
            select the model and voiceId which are required fields.
      title: CreateAgentRequestSynthesizerVoiceConfig0
    CreateAgentRequestSynthesizerVoiceConfigOneOf1Model:
      type: string
      enum:
        - waves
        - waves_lightning_large
      description: >-
        We currently support 3 types of models for the synthesizer. Waves, Waves
        Lightning Large and Waves Lightning Large Voice Clone. You can clone
        your voice using waves platform and use the voiceId for this field and
        select the model as waves_lightning_large_voice_clone to use your cloned
        voice.
      title: CreateAgentRequestSynthesizerVoiceConfigOneOf1Model
    CreateAgentRequestSynthesizerVoiceConfig1:
      type: object
      properties:
        model:
          $ref: >-
            #/components/schemas/CreateAgentRequestSynthesizerVoiceConfigOneOf1Model
          description: >-
            We currently support 3 types of models for the synthesizer. Waves,
            Waves Lightning Large and Waves Lightning Large Voice Clone. You can
            clone your voice using waves platform and use the voiceId for this
            field and select the model as waves_lightning_large_voice_clone to
            use your cloned voice.
        voiceId:
          type: string
          default: nyah
          description: The voice ID to use
      title: CreateAgentRequestSynthesizerVoiceConfig1
    CreateAgentRequestSynthesizerVoiceConfig:
      oneOf:
        - $ref: '#/components/schemas/CreateAgentRequestSynthesizerVoiceConfig0'
        - $ref: '#/components/schemas/CreateAgentRequestSynthesizerVoiceConfig1'
      title: CreateAgentRequestSynthesizerVoiceConfig
    CreateAgentRequestSynthesizerEnhancement:
      type: string
      enum:
        - '0'
        - '1'
        - '2'
      title: CreateAgentRequestSynthesizerEnhancement
    CreateAgentRequestSynthesizerSampleRate:
      type: string
      enum:
        - '8000'
        - '16000'
        - '24000'
        - '44100'
      description: Output audio sample rate in Hz.
      title: CreateAgentRequestSynthesizerSampleRate
    CreateAgentRequestSynthesizer:
      type: object
      properties:
        voiceConfig:
          $ref: '#/components/schemas/CreateAgentRequestSynthesizerVoiceConfig'
          default:
            model: waves_lightning_large
            voiceId: nyah
        speed:
          type: number
          format: double
          default: 1.2
        consistency:
          type: number
          format: double
          default: 0.5
        similarity:
          type: number
          format: double
          default: 0
        enhancement:
          $ref: '#/components/schemas/CreateAgentRequestSynthesizerEnhancement'
          default: 1
        sampleRate:
          $ref: '#/components/schemas/CreateAgentRequestSynthesizerSampleRate'
          default: 16000
          description: Output audio sample rate in Hz.
      description: >-
        Synthesizer configuration for the agent. You can configure the
        synthesizer to use different voices and models. Currently we support 3
        types of models for the synthesizer. Waves, Waves Lightning Large and
        Waves Lightning Large Voice Clone. You can clone your voice using waves
        platform https://waves.smallest.ai/voice-clone and use the voiceId for
        this field and select the model as waves_lightning_large_voice_clone to
        use your cloned voice. When updating the synthesizer configuration to
        voice clone model, you have to provide model and voiceId and gender all
        are required fields but when selecting the model as waves or waves and
        waves_lightning_large, you have to provide only model field and voiceId.
      title: CreateAgentRequestSynthesizer
    CreateAgentRequestSlmModel:
      type: string
      enum:
        - electron
        - gpt-4o
      default: electron
      description: >-
        The LLM model to use for the agent. LLM model will be used to generate
        the response and take decisions based on the user's query.
      title: CreateAgentRequestSlmModel
    CreateAgentRequestDefaultVariables:
      type: object
      properties: {}
      description: >-
        The default variables to use for the agent. These variables will be used
        if no variables are provided when initiating a conversation with the
        agent.
      title: CreateAgentRequestDefaultVariables
    CreateAgentRequestPreCallApiMethod:
      type: string
      enum:
        - GET
        - POST
        - PUT
        - DELETE
        - PATCH
      description: The HTTP method to use for the API call.
      title: CreateAgentRequestPreCallApiMethod
    CreateAgentRequestPreCallApiBody:
      type: object
      properties: {}
      description: Optional request body for POST/PUT/PATCH requests.
      title: CreateAgentRequestPreCallApiBody
    CreateAgentRequestPreCallApiQueryParams:
      type: object
      properties: {}
      description: Optional query parameters to include in the request URL.
      title: CreateAgentRequestPreCallApiQueryParams
    CreateAgentRequestPreCallApiResponseVariablesItems:
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
      title: CreateAgentRequestPreCallApiResponseVariablesItems
    CreateAgentRequestPreCallApi:
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
          $ref: '#/components/schemas/CreateAgentRequestPreCallApiMethod'
          description: The HTTP method to use for the API call.
        headers:
          type: object
          additionalProperties:
            type: string
          description: Optional HTTP headers to include in the request.
        body:
          $ref: '#/components/schemas/CreateAgentRequestPreCallApiBody'
          description: Optional request body for POST/PUT/PATCH requests.
        timeout:
          type: integer
          default: 5
          description: Timeout in seconds for the API call.
        queryParams:
          $ref: '#/components/schemas/CreateAgentRequestPreCallApiQueryParams'
          description: Optional query parameters to include in the request URL.
        responseVariables:
          type: array
          items:
            $ref: >-
              #/components/schemas/CreateAgentRequestPreCallApiResponseVariablesItems
          description: >-
            List of variables to extract from the API response using JSON path
            expressions.
      required:
        - url
        - method
      description: >-
        Configuration for an API call to be made before the call starts. The
        response variables can be injected into the agent's prompt.
      title: CreateAgentRequestPreCallApi
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    CreateAgentRequestSmartTurnConfig:
      type: object
      properties:
        isEnabled:
          type: boolean
        waitTimeInSecs:
          type: number
          format: double
          description: How long to wait after the user stops speaking before responding.
      description: >-
        Smart turn-detection configuration. When enabled, the agent uses an
        additional model to decide whether the user has finished a turn.
      title: CreateAgentRequestSmartTurnConfig
    CreateAgentRequestVoiceDetectionConfig:
      type: object
      properties:
        confidence:
          type: number
          format: double
          description: Minimum VAD confidence threshold to register speech.
        minVolume:
          type: number
          format: double
          description: Minimum input volume threshold to register speech.
        triggerTimeInSecs:
          type: number
          format: double
          description: >-
            How long sustained speech must be detected before turning the VAD
            on.
        releaseTimeInSecs:
          type: number
          format: double
          description: How long after silence before the VAD turns off.
      description: >-
        Voice activity detection (VAD) configuration. Controls how the agent
        decides when speech is present.
      title: CreateAgentRequestVoiceDetectionConfig
    CreateAgentRequestVoiceMailDetectionConfig:
      type: object
      properties:
        enabled:
          type: boolean
        endText:
          type: string
          description: Message played before hanging up when voicemail is detected.
      description: >-
        Voicemail-detection configuration. When the call hits a voicemail tone,
        the agent plays `endText` and ends the call.
      title: CreateAgentRequestVoiceMailDetectionConfig
    CreateAgentRequestDenoisingConfig:
      type: object
      properties:
        isEnabled:
          type: boolean
      description: Background-noise denoising configuration for the agent's input audio.
      title: CreateAgentRequestDenoisingConfig
    CreateAgentRequestRedactionConfig:
      type: object
      properties:
        isEnabled:
          type: boolean
      description: >-
        PII redaction configuration. When enabled, personally identifiable
        information is redacted from transcripts before storage.
      title: CreateAgentRequestRedactionConfig
    CreateAgentRequestPronunciationDictsItems:
      type: object
      properties:
        word:
          type: string
          description: The word to override.
        pronunciation:
          type: string
          description: How the word should be pronounced (phonetic spelling).
      required:
        - word
        - pronunciation
      title: CreateAgentRequestPronunciationDictsItems
    CreateAgentRequestLlmIdleTimeoutConfig:
      type: object
      properties:
        chatTimeoutTimeInSecs:
          type: number
          format: double
          description: LLM idle timeout for chat conversations, in seconds.
        webcallTimeoutTimeInSecs:
          type: number
          format: double
          description: LLM idle timeout for web calls, in seconds.
        telephonyTimeoutTimeInSecs:
          type: number
          format: double
          description: LLM idle timeout for telephony calls, in seconds.
        maxRetries:
          type: number
          format: double
          description: >-
            Maximum number of LLM-idle retries before terminating the call.
            System-defined min/max.
      description: >-
        Timeout configuration for the LLM stage of a conversation. Triggers a
        retry or call termination when the LLM does not respond within the
        configured window.
      title: CreateAgentRequestLlmIdleTimeoutConfig
    CreateAgentRequestSessionTimeoutConfig:
      type: object
      properties:
        timeoutTimeInSecs:
          type: number
          format: double
          default: 1800
          description: >-
            Maximum session duration in seconds (max 1 hour). Defaults to 1800
            (30 minutes).
      description: >-
        Maximum duration of a conversation session. The call ends after this
        elapsed time even if active.
      title: CreateAgentRequestSessionTimeoutConfig
    CreateAgentRequestTimezone:
      type: object
      properties:
        label:
          type: string
          description: IANA timezone label (e.g. `America/New_York`).
        offset:
          type: number
          format: double
          description: UTC offset in minutes (e.g. -300 for EST).
      description: >-
        Timezone applied to scheduled actions and timestamps the agent reports
        to the user.
      title: CreateAgentRequestTimezone
    CreateAgentRequest:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        backgroundSound:
          $ref: '#/components/schemas/CreateAgentRequestBackgroundSound'
          default: ''
          description: >-
            Ambient background sound during calls. Options: '' (none), 'office',
            'cafe', 'call_center', 'static'.
        language:
          $ref: '#/components/schemas/CreateAgentRequestLanguage'
          description: >-
            Language configuration for the agent. You can enable or disable
            language switching for the agent. This will be used to determine the
            language of the agent.
        synthesizer:
          $ref: '#/components/schemas/CreateAgentRequestSynthesizer'
          description: >-
            Synthesizer configuration for the agent. You can configure the
            synthesizer to use different voices and models. Currently we support
            3 types of models for the synthesizer. Waves, Waves Lightning Large
            and Waves Lightning Large Voice Clone. You can clone your voice
            using waves platform https://waves.smallest.ai/voice-clone and use
            the voiceId for this field and select the model as
            waves_lightning_large_voice_clone to use your cloned voice. When
            updating the synthesizer configuration to voice clone model, you
            have to provide model and voiceId and gender all are required fields
            but when selecting the model as waves or waves and
            waves_lightning_large, you have to provide only model field and
            voiceId.
        globalKnowledgeBaseId:
          type: string
          description: >-
            The global knowledge base ID of the agent. You can create a global
            knowledge base by using the /knowledgebase endpoint and assign it to
            the agent. The agent will use this knowledge base for its responses.
        slmModel:
          $ref: '#/components/schemas/CreateAgentRequestSlmModel'
          default: electron
          description: >-
            The LLM model to use for the agent. LLM model will be used to
            generate the response and take decisions based on the user's query.
        defaultVariables:
          $ref: '#/components/schemas/CreateAgentRequestDefaultVariables'
          description: >-
            The default variables to use for the agent. These variables will be
            used if no variables are provided when initiating a conversation
            with the agent.
        preCallAPI:
          $ref: '#/components/schemas/CreateAgentRequestPreCallApi'
          description: >-
            Configuration for an API call to be made before the call starts. The
            response variables can be injected into the agent's prompt.
        globalPrompt:
          type: string
          description: >
            Set global instructions for your agent's personality, role, and
            behavior throughout conversations.

            Note: Only used for workflow_graph agents.
        telephonyProductId:
          type: string
          description: >-
            The telephony product ID of the agent. This is the product ID of the
            telephony product that will be used to make the outbound call. You
            can buy telephone number and assign it to the agent.
        workflowType:
          $ref: '#/components/schemas/WorkflowType'
          description: >-
            The type of workflow to create for the agent. Defaults to
            workflow_graph if not specified.
        firstMessage:
          type: string
          description: The first message the agent sends when a conversation starts.
        muteUserUntilFirstBotResponse:
          type: boolean
          description: >-
            When true, the user's audio is muted until the agent has finished
            its first response.
        allowInterruptions:
          type: boolean
          description: Whether the user can interrupt the agent while it is speaking.
        waitForUserToSpeakFirst:
          type: boolean
          description: >-
            When true, the agent waits for the user to speak before sending the
            first message.
        interruptionBackoffTimer:
          type: number
          format: double
          description: >-
            Seconds the agent waits after being interrupted before resuming
            speech.
        smartTurnConfig:
          $ref: '#/components/schemas/CreateAgentRequestSmartTurnConfig'
          description: >-
            Smart turn-detection configuration. When enabled, the agent uses an
            additional model to decide whether the user has finished a turn.
        voiceDetectionConfig:
          $ref: '#/components/schemas/CreateAgentRequestVoiceDetectionConfig'
          description: >-
            Voice activity detection (VAD) configuration. Controls how the agent
            decides when speech is present.
        voiceMailDetectionConfig:
          $ref: '#/components/schemas/CreateAgentRequestVoiceMailDetectionConfig'
          description: >-
            Voicemail-detection configuration. When the call hits a voicemail
            tone, the agent plays `endText` and ends the call.
        denoisingConfig:
          $ref: '#/components/schemas/CreateAgentRequestDenoisingConfig'
          description: >-
            Background-noise denoising configuration for the agent's input
            audio.
        redactionConfig:
          $ref: '#/components/schemas/CreateAgentRequestRedactionConfig'
          description: >-
            PII redaction configuration. When enabled, personally identifiable
            information is redacted from transcripts before storage.
        pronunciationDicts:
          type: array
          items:
            $ref: '#/components/schemas/CreateAgentRequestPronunciationDictsItems'
          description: >-
            Pronunciation overrides — words the TTS engine should pronounce
            differently from its default.
        llmIdleTimeoutConfig:
          $ref: '#/components/schemas/CreateAgentRequestLlmIdleTimeoutConfig'
          description: >-
            Timeout configuration for the LLM stage of a conversation. Triggers
            a retry or call termination when the LLM does not respond within the
            configured window.
        sessionTimeoutConfig:
          $ref: '#/components/schemas/CreateAgentRequestSessionTimeoutConfig'
          description: >-
            Maximum duration of a conversation session. The call ends after this
            elapsed time even if active.
        timezone:
          $ref: '#/components/schemas/CreateAgentRequestTimezone'
          description: >-
            Timezone applied to scheduled actions and timestamps the agent
            reports to the user.
      required:
        - name
      title: CreateAgentRequest
    Agents_createANewAgent_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: string
          description: The ID of the created agent
      title: Agents_createANewAgent_Response_201
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
    await client.atoms.agents.createANewAgent({
        name: "string",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agents.create_a_new_agent(
    name="string",
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

	url := "https://api.smallest.ai/atoms/v1/agent"

	payload := strings.NewReader("{\n  \"name\": \"string\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"name\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/agent")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"name\": \"string\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/agent', [
  'body' => '{
  "name": "string"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"name\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["name": "string"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent")! as URL,
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
