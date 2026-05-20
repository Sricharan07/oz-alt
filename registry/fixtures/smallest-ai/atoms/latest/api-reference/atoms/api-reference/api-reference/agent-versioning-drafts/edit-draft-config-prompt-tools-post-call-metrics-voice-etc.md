> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Edit draft config (prompt, tools, post-call metrics, voice, etc.)

PATCH https://api.smallest.ai/atoms/v1/agent/{id}/drafts/{draftId}/config
Content-Type: application/json

Update the configuration of a draft. This single endpoint is how every
agent-level config field is changed: prompt, tools, voice, language,
**post-call analytics (disposition metrics)**, and more. There is no
standalone post-call-analytics endpoint — it lives here as the
`postCallAnalyticsConfig` body field.

## Post-Call Analytics

Pass a `postCallAnalyticsConfig` object to configure disposition
metrics (STRING, BOOLEAN, INTEGER, ENUM, DATETIME) that are
automatically extracted from each completed call, along with the
`useInternalAnalyticsModel` and `useReasoningModel` flags. See the
[Post-Call Metrics guide](/atoms/atoms-platform/features/post-call-metrics) for a
full Python walkthrough and disposition metric schema reference.

## Full payload

Accepts the full agent-shaped config payload (language, synthesizer,
slmModel, defaultVariables, preCallAPI, etc.) plus two draft-specific
fields:

- `singlePromptConfig` — prompt and tools (end_call, transfer_call,
  api_call, extract_dynamic_variables, knowledge_base_search).
- `postCallAnalyticsConfig` — disposition metrics + analytics/
  reasoning model flags.

Each PATCH increments the draft's revision counter. Config is not
live until the draft is published and activated (see
`/drafts/{draftId}/publish` and `/versions/{versionId}/activate`).

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-versioning-drafts/edit-draft-config-prompt-tools-post-call-metrics-voice-etc

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/{id}/drafts/{draftId}/config:
    patch:
      operationId: edit-draft-config-prompt-tools-post-call-metrics-voice-etc
      summary: Edit draft config (prompt, tools, post-call metrics, voice, etc.)
      description: >
        Update the configuration of a draft. This single endpoint is how every

        agent-level config field is changed: prompt, tools, voice, language,

        **post-call analytics (disposition metrics)**, and more. There is no

        standalone post-call-analytics endpoint — it lives here as the

        `postCallAnalyticsConfig` body field.

        ## Post-Call Analytics

        Pass a `postCallAnalyticsConfig` object to configure disposition

        metrics (STRING, BOOLEAN, INTEGER, ENUM, DATETIME) that are

        automatically extracted from each completed call, along with the

        `useInternalAnalyticsModel` and `useReasoningModel` flags. See the

        [Post-Call Metrics
        guide](/atoms/atoms-platform/features/post-call-metrics) for a

        full Python walkthrough and disposition metric schema reference.

        ## Full payload

        Accepts the full agent-shaped config payload (language, synthesizer,

        slmModel, defaultVariables, preCallAPI, etc.) plus two draft-specific

        fields:

        - `singlePromptConfig` — prompt and tools (end_call, transfer_call,
          api_call, extract_dynamic_variables, knowledge_base_search).
        - `postCallAnalyticsConfig` — disposition metrics + analytics/
          reasoning model flags.

        Each PATCH increments the draft's revision counter. Config is not

        live until the draft is published and activated (see

        `/drafts/{draftId}/publish` and `/versions/{versionId}/activate`).
      tags:
        - subpackage_agentVersioningDrafts
      parameters:
        - name: id
          in: path
          description: The agent ID
          required: true
          schema:
            type: string
        - name: draftId
          in: path
          description: The draft ID
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
          description: Draft config updated successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Agent Versioning -
                  Drafts_editDraftConfigPromptToolsPostCallMetricsVoiceEtc_Response_200
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
              $ref: '#/components/schemas/DraftConfigRequest'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    DraftConfigRequestBackgroundSound:
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
      title: DraftConfigRequestBackgroundSound
    DraftConfigRequestLanguageEnabled:
      type: string
      enum:
        - en
        - hi
        - ta
      default: en
      description: >-
        The language of the agent. Supported: 'en' (English), 'hi' (Hindi), 'ta'
        (Tamil).
      title: DraftConfigRequestLanguageEnabled
    DraftConfigRequestLanguageSwitching:
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
      title: DraftConfigRequestLanguageSwitching
    DraftConfigRequestLanguage:
      type: object
      properties:
        enabled:
          $ref: '#/components/schemas/DraftConfigRequestLanguageEnabled'
          default: en
          description: >-
            The language of the agent. Supported: 'en' (English), 'hi' (Hindi),
            'ta' (Tamil).
        switching:
          $ref: '#/components/schemas/DraftConfigRequestLanguageSwitching'
          description: >-
            Language switching configuration for the agent. If enabled, the
            agent will be able to switch between languages based on the user's
            language.
      description: >-
        Language configuration for the agent. You can enable or disable language
        switching for the agent. This will be used to determine the language of
        the agent.
      title: DraftConfigRequestLanguage
    DraftConfigRequestSynthesizerVoiceConfigOneOf0Model:
      type: string
      enum:
        - waves_lightning_large_voice_clone
      description: >-
        We currently support 3 types of models for the synthesizer. Waves, Waves
        Lightning Large and Waves Lightning Large Voice Clone. You can clone
        your voice using waves platform and use the voiceId for this field and
        select the model as waves_lightning_large_voice_clone to use your cloned
        voice.
      title: DraftConfigRequestSynthesizerVoiceConfigOneOf0Model
    DraftConfigRequestSynthesizerVoiceConfigOneOf0Gender:
      type: string
      enum:
        - male
        - female
      description: >-
        The gender of the synthesizer. When selecting gender, you have to select
        the model and voiceId which are required fields.
      title: DraftConfigRequestSynthesizerVoiceConfigOneOf0Gender
    DraftConfigRequestSynthesizerVoiceConfig0:
      type: object
      properties:
        model:
          $ref: >-
            #/components/schemas/DraftConfigRequestSynthesizerVoiceConfigOneOf0Model
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
            #/components/schemas/DraftConfigRequestSynthesizerVoiceConfigOneOf0Gender
          description: >-
            The gender of the synthesizer. When selecting gender, you have to
            select the model and voiceId which are required fields.
      title: DraftConfigRequestSynthesizerVoiceConfig0
    DraftConfigRequestSynthesizerVoiceConfigOneOf1Model:
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
      title: DraftConfigRequestSynthesizerVoiceConfigOneOf1Model
    DraftConfigRequestSynthesizerVoiceConfig1:
      type: object
      properties:
        model:
          $ref: >-
            #/components/schemas/DraftConfigRequestSynthesizerVoiceConfigOneOf1Model
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
      title: DraftConfigRequestSynthesizerVoiceConfig1
    DraftConfigRequestSynthesizerVoiceConfig:
      oneOf:
        - $ref: '#/components/schemas/DraftConfigRequestSynthesizerVoiceConfig0'
        - $ref: '#/components/schemas/DraftConfigRequestSynthesizerVoiceConfig1'
      title: DraftConfigRequestSynthesizerVoiceConfig
    DraftConfigRequestSynthesizerEnhancement:
      type: string
      enum:
        - '0'
        - '1'
        - '2'
      title: DraftConfigRequestSynthesizerEnhancement
    DraftConfigRequestSynthesizerSampleRate:
      type: string
      enum:
        - '8000'
        - '16000'
        - '24000'
        - '44100'
      description: Output audio sample rate in Hz.
      title: DraftConfigRequestSynthesizerSampleRate
    DraftConfigRequestSynthesizer:
      type: object
      properties:
        voiceConfig:
          $ref: '#/components/schemas/DraftConfigRequestSynthesizerVoiceConfig'
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
          $ref: '#/components/schemas/DraftConfigRequestSynthesizerEnhancement'
          default: 1
        sampleRate:
          $ref: '#/components/schemas/DraftConfigRequestSynthesizerSampleRate'
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
      title: DraftConfigRequestSynthesizer
    DraftConfigRequestSlmModel:
      type: string
      enum:
        - electron
        - gpt-4o
      default: electron
      description: >-
        The LLM model to use for the agent. LLM model will be used to generate
        the response and take decisions based on the user's query.
      title: DraftConfigRequestSlmModel
    DraftConfigRequestDefaultVariables:
      type: object
      properties: {}
      description: >-
        The default variables to use for the agent. These variables will be used
        if no variables are provided when initiating a conversation with the
        agent.
      title: DraftConfigRequestDefaultVariables
    DraftConfigRequestPreCallApiMethod:
      type: string
      enum:
        - GET
        - POST
        - PUT
        - DELETE
        - PATCH
      description: The HTTP method to use for the API call.
      title: DraftConfigRequestPreCallApiMethod
    DraftConfigRequestPreCallApiBody:
      type: object
      properties: {}
      description: Optional request body for POST/PUT/PATCH requests.
      title: DraftConfigRequestPreCallApiBody
    DraftConfigRequestPreCallApiQueryParams:
      type: object
      properties: {}
      description: Optional query parameters to include in the request URL.
      title: DraftConfigRequestPreCallApiQueryParams
    DraftConfigRequestPreCallApiResponseVariablesItems:
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
      title: DraftConfigRequestPreCallApiResponseVariablesItems
    DraftConfigRequestPreCallApi:
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
          $ref: '#/components/schemas/DraftConfigRequestPreCallApiMethod'
          description: The HTTP method to use for the API call.
        headers:
          type: object
          additionalProperties:
            type: string
          description: Optional HTTP headers to include in the request.
        body:
          $ref: '#/components/schemas/DraftConfigRequestPreCallApiBody'
          description: Optional request body for POST/PUT/PATCH requests.
        timeout:
          type: integer
          default: 5
          description: Timeout in seconds for the API call.
        queryParams:
          $ref: '#/components/schemas/DraftConfigRequestPreCallApiQueryParams'
          description: Optional query parameters to include in the request URL.
        responseVariables:
          type: array
          items:
            $ref: >-
              #/components/schemas/DraftConfigRequestPreCallApiResponseVariablesItems
          description: >-
            List of variables to extract from the API response using JSON path
            expressions.
      required:
        - url
        - method
      description: >-
        Configuration for an API call to be made before the call starts. The
        response variables can be injected into the agent's prompt.
      title: DraftConfigRequestPreCallApi
    WorkflowType:
      type: string
      enum:
        - workflow_graph
        - single_prompt
      description: >-
        The type of workflow configuration. workflow_graph uses a node-based
        visual workflow, single_prompt uses a simple prompt-based configuration.
      title: WorkflowType
    DraftConfigRequestSmartTurnConfig:
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
      title: DraftConfigRequestSmartTurnConfig
    DraftConfigRequestVoiceDetectionConfig:
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
      title: DraftConfigRequestVoiceDetectionConfig
    DraftConfigRequestVoiceMailDetectionConfig:
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
      title: DraftConfigRequestVoiceMailDetectionConfig
    DraftConfigRequestDenoisingConfig:
      type: object
      properties:
        isEnabled:
          type: boolean
      description: Background-noise denoising configuration for the agent's input audio.
      title: DraftConfigRequestDenoisingConfig
    DraftConfigRequestRedactionConfig:
      type: object
      properties:
        isEnabled:
          type: boolean
      description: >-
        PII redaction configuration. When enabled, personally identifiable
        information is redacted from transcripts before storage.
      title: DraftConfigRequestRedactionConfig
    DraftConfigRequestPronunciationDictsItems:
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
      title: DraftConfigRequestPronunciationDictsItems
    DraftConfigRequestLlmIdleTimeoutConfig:
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
      title: DraftConfigRequestLlmIdleTimeoutConfig
    DraftConfigRequestSessionTimeoutConfig:
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
      title: DraftConfigRequestSessionTimeoutConfig
    DraftConfigRequestTimezone:
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
      title: DraftConfigRequestTimezone
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
    DraftConfigRequest:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        backgroundSound:
          $ref: '#/components/schemas/DraftConfigRequestBackgroundSound'
          default: ''
          description: >-
            Ambient background sound during calls. Options: '' (none), 'office',
            'cafe', 'call_center', 'static'.
        language:
          $ref: '#/components/schemas/DraftConfigRequestLanguage'
          description: >-
            Language configuration for the agent. You can enable or disable
            language switching for the agent. This will be used to determine the
            language of the agent.
        synthesizer:
          $ref: '#/components/schemas/DraftConfigRequestSynthesizer'
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
          $ref: '#/components/schemas/DraftConfigRequestSlmModel'
          default: electron
          description: >-
            The LLM model to use for the agent. LLM model will be used to
            generate the response and take decisions based on the user's query.
        defaultVariables:
          $ref: '#/components/schemas/DraftConfigRequestDefaultVariables'
          description: >-
            The default variables to use for the agent. These variables will be
            used if no variables are provided when initiating a conversation
            with the agent.
        preCallAPI:
          $ref: '#/components/schemas/DraftConfigRequestPreCallApi'
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
          $ref: '#/components/schemas/DraftConfigRequestSmartTurnConfig'
          description: >-
            Smart turn-detection configuration. When enabled, the agent uses an
            additional model to decide whether the user has finished a turn.
        voiceDetectionConfig:
          $ref: '#/components/schemas/DraftConfigRequestVoiceDetectionConfig'
          description: >-
            Voice activity detection (VAD) configuration. Controls how the agent
            decides when speech is present.
        voiceMailDetectionConfig:
          $ref: '#/components/schemas/DraftConfigRequestVoiceMailDetectionConfig'
          description: >-
            Voicemail-detection configuration. When the call hits a voicemail
            tone, the agent plays `endText` and ends the call.
        denoisingConfig:
          $ref: '#/components/schemas/DraftConfigRequestDenoisingConfig'
          description: >-
            Background-noise denoising configuration for the agent's input
            audio.
        redactionConfig:
          $ref: '#/components/schemas/DraftConfigRequestRedactionConfig'
          description: >-
            PII redaction configuration. When enabled, personally identifiable
            information is redacted from transcripts before storage.
        pronunciationDicts:
          type: array
          items:
            $ref: '#/components/schemas/DraftConfigRequestPronunciationDictsItems'
          description: >-
            Pronunciation overrides — words the TTS engine should pronounce
            differently from its default.
        llmIdleTimeoutConfig:
          $ref: '#/components/schemas/DraftConfigRequestLlmIdleTimeoutConfig'
          description: >-
            Timeout configuration for the LLM stage of a conversation. Triggers
            a retry or call termination when the LLM does not respond within the
            configured window.
        sessionTimeoutConfig:
          $ref: '#/components/schemas/DraftConfigRequestSessionTimeoutConfig'
          description: >-
            Maximum duration of a conversation session. The call ends after this
            elapsed time even if active.
        timezone:
          $ref: '#/components/schemas/DraftConfigRequestTimezone'
          description: >-
            Timezone applied to scheduled actions and timestamps the agent
            reports to the user.
        singlePromptConfig:
          $ref: '#/components/schemas/SinglePromptConfig'
        postCallAnalyticsConfig:
          $ref: '#/components/schemas/PostCallAnalyticsConfig'
      required:
        - name
      description: >
        Config payload for editing a draft via `PATCH
        /agent/{id}/drafts/{draftId}/config`.

        Accepts the same shape as the legacy `PATCH /agent/{id}` body plus two

        versioning-era fields — `singlePromptConfig` (prompt + tools) and

        `postCallAnalyticsConfig`. All fields are optional; a draft save may
        update

        any subset.
      title: DraftConfigRequest
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
    Agent Versioning - Drafts_editDraftConfigPromptToolsPostCallMetricsVoiceEtc_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/AgentVersion'
      title: >-
        Agent Versioning -
        Drafts_editDraftConfigPromptToolsPostCallMetricsVoiceEtc_Response_200
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

url = "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config"

payload = { "name": "string" }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config';
const options = {
  method: 'PATCH',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"name":"string"}'
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

	url := "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config"

	payload := strings.NewReader("{\n  \"name\": \"string\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"name\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"name\": \"string\"\n}")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config");
var request = new RestRequest(Method.PATCH);
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/60d0fe4f5311236168a109ca/drafts/draftId/config")! as URL,
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
