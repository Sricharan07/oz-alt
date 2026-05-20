> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# pre-conversation

POST

Fired **before** the agent begins speaking. Use this to enrich CRM
data, log call attempts, or gate outbound calls.

Does **not** contain `callData`, `transcript`, `variables`, `analytics`,
or `recordingUrl`. `callData` is on `post-conversation` and
`analytics-completed`; `transcript`, `variables`, and `recordingUrl`
are only on `post-conversation`; `analytics` is only on
`analytics-completed`.

For the full field-level reference, see the [Webhooks guide](/atoms/atoms-platform/features/webhooks).

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/webhook-event-pre-conversation

## OpenAPI 3.1 Webhook Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths: {}
webhooks:
  webhook-event-pre-conversation:
    post:
      operationId: webhook-event-pre-conversation
      summary: pre-conversation
      description: >
        Fired **before** the agent begins speaking. Use this to enrich CRM

        data, log call attempts, or gate outbound calls.

        Does **not** contain `callData`, `transcript`, `variables`, `analytics`,

        or `recordingUrl`. `callData` is on `post-conversation` and

        `analytics-completed`; `transcript`, `variables`, and `recordingUrl`

        are only on `post-conversation`; `analytics` is only on

        `analytics-completed`.

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
              $ref: '#/components/schemas/WebhookEventPreConversation'
components:
  schemas:
    WebhookEventPreConversationMetadataEventType:
      type: string
      enum:
        - pre-conversation
      title: WebhookEventPreConversationMetadataEventType
    WebhookEventPreConversationMetadata:
      type: object
      properties:
        agentId:
          type: string
          description: The Atoms agent ID that handled the call.
        eventType:
          $ref: '#/components/schemas/WebhookEventPreConversationMetadataEventType'
        conversationType:
          type: string
          description: 'Channel type. Known values: `telephonyOutbound`, `telephonyInbound`.'
        toPhone:
          type: string
          description: Destination phone number in E.164 format.
        fromPhone:
          type: string
          description: Originating phone number in E.164 format.
        callId:
          type: string
          description: Unique call identifier.
      required:
        - agentId
        - eventType
        - conversationType
        - toPhone
        - fromPhone
        - callId
      title: WebhookEventPreConversationMetadata
    WebhookEventPreConversation:
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
          $ref: '#/components/schemas/WebhookEventPreConversationMetadata'
      required:
        - url
        - description
        - event
        - id
        - metadata
      description: |
        Fired **before** the agent begins speaking. Use this to enrich CRM data,
        log call attempts, or gate outbound calls.

        Does **not** contain `callData`, `transcript`, `variables`, `analytics`,
        or `recordingUrl`. `callData` is on `post-conversation` and
        `analytics-completed`; `transcript`, `variables`, and `recordingUrl`
        are only on `post-conversation`; `analytics` is only on
        `analytics-completed`.
      title: WebhookEventPreConversation

```
