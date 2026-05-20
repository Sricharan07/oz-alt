> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# post-conversation

POST

Fired **after** the call ends. Contains the full transcript, call
metadata, recording URL, and all agent variables that were in scope
during the conversation.

For the full field-level reference, see the [Webhooks guide](/atoms/atoms-platform/features/webhooks).

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/webhook-event-post-conversation

## OpenAPI 3.1 Webhook Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths: {}
webhooks:
  webhook-event-post-conversation:
    post:
      operationId: webhook-event-post-conversation
      summary: post-conversation
      description: >
        Fired **after** the call ends. Contains the full transcript, call

        metadata, recording URL, and all agent variables that were in scope

        during the conversation.

        For the full field-level reference, see the [Webhooks
        guide](/atoms/atoms-platform/features/webhooks).
      responses:
        '200':
          description: Webhook received successfully
      requestBody:
        description: Event body delivered to your configured webhook URL.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookEventPostConversation'
components:
  schemas:
    WebhookEventPostConversationMetadataEventType:
      type: string
      enum:
        - post-conversation
      title: WebhookEventPostConversationMetadataEventType
    WebhookEventCallDataCallStatus:
      type: string
      enum:
        - completed
        - no-answer
        - busy
        - failed
        - canceled
      description: Terminal status.
      title: WebhookEventCallDataCallStatus
    WebhookEventCallDataCallDirection:
      type: string
      enum:
        - telephony_outbound
        - telephony_inbound
      description: |
        Call direction. Present on `post-conversation`; may be absent on
        `analytics-completed`.
      title: WebhookEventCallDataCallDirection
    WebhookEventCallData:
      type: object
      properties:
        fromNumber:
          type: string
          description: Originating phone number in E.164 format.
        toNumber:
          type: string
          description: Destination phone number in E.164 format.
        callDuration:
          type: number
          format: double
          description: Total call duration in **seconds** (float).
        callStatus:
          $ref: '#/components/schemas/WebhookEventCallDataCallStatus'
          description: Terminal status.
        callDirection:
          $ref: '#/components/schemas/WebhookEventCallDataCallDirection'
          description: |
            Call direction. Present on `post-conversation`; may be absent on
            `analytics-completed`.
        answerTime:
          type: string
          format: date-time
          description: ISO 8601 timestamp when the call was answered (UTC).
        endTime:
          type: string
          format: date-time
          description: ISO 8601 timestamp when the call ended (UTC).
      required:
        - fromNumber
        - toNumber
        - callDuration
        - callStatus
        - answerTime
        - endTime
      description: |
        Call-level metadata shared by `post-conversation` and
        `analytics-completed` events. In `analytics-completed`, the
        `callDirection` field may be absent.
      title: WebhookEventCallData
    WebhookEventTranscriptTurnRole:
      type: string
      enum:
        - agent
        - user
      description: Speaker role.
      title: WebhookEventTranscriptTurnRole
    WebhookEventTranscriptTurn:
      type: object
      properties:
        role:
          $ref: '#/components/schemas/WebhookEventTranscriptTurnRole'
          description: Speaker role.
        content:
          type: string
          description: The spoken text for this turn.
        timestamp:
          type: string
          format: date-time
          description: ISO 8601 timestamp of when this turn began (UTC).
      required:
        - role
        - content
        - timestamp
      description: One speaking turn in a `post-conversation` transcript.
      title: WebhookEventTranscriptTurn
    WebhookEventPostConversationMetadata:
      type: object
      properties:
        agentId:
          type: string
        eventType:
          $ref: '#/components/schemas/WebhookEventPostConversationMetadataEventType'
        conversationType:
          type: string
        callId:
          type: string
        recordingUrl:
          type: string
          format: uri
          description: URL to the composite call recording (`.wav`).
        callData:
          $ref: '#/components/schemas/WebhookEventCallData'
        transcript:
          type: array
          items:
            $ref: '#/components/schemas/WebhookEventTranscriptTurn'
          description: Ordered list of transcript turns.
        variables:
          type: object
          additionalProperties:
            description: Any type
          description: >
            Flat key-value map of all agent variables in scope during the call.

            **This object is fully dynamic.** Keys and values are entirely
            determined by

            the agent's configuration; they are not fixed by the platform. New
            keys can

            appear at any time. Store as JSON and iterate keys — do not
            hard-code column

            mappings. Common platform keys include `agent_name`,
            `customer_name`,

            `current_date`, `default_language`; domain-specific keys (e.g.
            `due_amount`,

            `bank_name`) come from your agent's prompt configuration.
      required:
        - agentId
        - eventType
        - conversationType
        - callId
        - recordingUrl
        - callData
        - transcript
        - variables
      title: WebhookEventPostConversationMetadata
    WebhookEventPostConversation:
      type: object
      properties:
        url:
          type: string
          description: The webhook URL endpoint that received the event.
        description:
          type: string
          description: >-
            Human-readable label configured on the webhook (e.g. "Debt
            Collection Agent's Endpoint").
        event:
          type: string
          description: Event identifier in the form `{agentId}.{eventType}`.
        id:
          type: string
          description: Unique webhook delivery ID (separate from `metadata.callId`).
        metadata:
          $ref: '#/components/schemas/WebhookEventPostConversationMetadata'
      required:
        - url
        - description
        - event
        - id
        - metadata
      description: |
        Fired **after** the call ends. Contains the full transcript, call
        metadata, recording URL, and all agent variables that were in scope
        during the conversation.
      title: WebhookEventPostConversation

```
