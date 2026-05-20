> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# analytics-completed

POST

Fired **after** Atoms finishes running the configured disposition and
success metrics on the transcript. Arrives some time after
`post-conversation`.

For the full field-level reference, see the [Webhooks guide](/atoms/atoms-platform/features/webhooks).

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/webhooks/webhook-event-analytics-completed

## OpenAPI 3.1 Webhook Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths: {}
webhooks:
  webhook-event-analytics-completed:
    post:
      operationId: webhook-event-analytics-completed
      summary: analytics-completed
      description: >
        Fired **after** Atoms finishes running the configured disposition and

        success metrics on the transcript. Arrives some time after

        `post-conversation`.

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
              $ref: '#/components/schemas/WebhookEventAnalyticsCompleted'
components:
  schemas:
    WebhookEventAnalyticsCompletedMetadataEventType:
      type: string
      enum:
        - analytics-completed
      title: WebhookEventAnalyticsCompletedMetadataEventType
    WebhookEventAnalyticsMetricValue:
      oneOf:
        - type: integer
        - type: string
        - type: boolean
      description: |
        The evaluated result. Type depends on `dispositionMetricType`.
      title: WebhookEventAnalyticsMetricValue
    WebhookEventAnalyticsMetricDispositionMetricType:
      type: string
      enum:
        - INTEGER
        - STRING
        - BOOLEAN
      description: Data type of `value`.
      title: WebhookEventAnalyticsMetricDispositionMetricType
    WebhookEventAnalyticsMetric:
      type: object
      properties:
        identifier:
          type: string
          description: >-
            Machine-readable metric name (e.g. `turn_taking_balance`,
            `escalation_needed`).
        value:
          $ref: '#/components/schemas/WebhookEventAnalyticsMetricValue'
          description: |
            The evaluated result. Type depends on `dispositionMetricType`.
        confidence:
          type: number
          format: double
          description: Confidence score (0–1).
        reasoning:
          type: string
          description: LLM-generated explanation for the assigned value.
        dispositionMetricPrompt:
          type: string
          description: The prompt/question that was used to evaluate this metric.
        dispositionMetricType:
          $ref: >-
            #/components/schemas/WebhookEventAnalyticsMetricDispositionMetricType
          description: Data type of `value`.
      required:
        - identifier
        - value
        - confidence
        - reasoning
        - dispositionMetricPrompt
        - dispositionMetricType
      description: |
        A single disposition or success metric computed by the
        `analytics-completed` event. The set of metrics is configured
        per-agent and can vary.
      title: WebhookEventAnalyticsMetric
    WebhookEventAnalyticsCompletedMetadataAnalytics:
      type: object
      properties:
        summary:
          type: string
          description: LLM-generated plain-text summary of the call.
        dispositionMetrics:
          type: array
          items:
            $ref: '#/components/schemas/WebhookEventAnalyticsMetric'
        successMetrics:
          type: array
          items:
            $ref: '#/components/schemas/WebhookEventAnalyticsMetric'
          description: Same schema as `dispositionMetrics`. May be empty.
      required:
        - summary
        - dispositionMetrics
        - successMetrics
      title: WebhookEventAnalyticsCompletedMetadataAnalytics
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
    WebhookEventAnalyticsCompletedMetadata:
      type: object
      properties:
        agentId:
          type: string
        eventType:
          $ref: '#/components/schemas/WebhookEventAnalyticsCompletedMetadataEventType'
        conversationType:
          type: string
        callId:
          type: string
        analytics:
          $ref: '#/components/schemas/WebhookEventAnalyticsCompletedMetadataAnalytics'
        callData:
          $ref: '#/components/schemas/WebhookEventCallData'
      required:
        - agentId
        - eventType
        - conversationType
        - callId
        - analytics
        - callData
      title: WebhookEventAnalyticsCompletedMetadata
    WebhookEventAnalyticsCompleted:
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
          $ref: '#/components/schemas/WebhookEventAnalyticsCompletedMetadata'
      required:
        - url
        - description
        - event
        - id
        - metadata
      description: |
        Fired **after** Atoms finishes running the configured disposition and
        success metrics on the transcript. Arrives some time after
        `post-conversation`.
      title: WebhookEventAnalyticsCompleted

```
