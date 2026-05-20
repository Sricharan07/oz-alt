> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Text to Speech (WebSocket)

GET /waves/v1/lightning-v2/get_speech/stream

The Lightning v2 WebSocket API provides real-time text-to-speech streaming capabilities with high-quality voice synthesis. This API uses WebSocket to deliver audio chunks as they're generated, enabling low-latency audio playback without waiting for the entire audio file to process. Perfect for interactive applications, voice assistants, and real-time communication systems that require immediate audio feedback. For an end-to-end example of how to use the Lightning v2 WebSocket API, check out [Text to Speech (WS) Example](https://github.com/smallest-inc/waves-examples/tree/main/lightning_v2/ws_streaming)

Reference: https://docs.smallest.ai/waves/v-3-0-1/api-reference/api-reference/lightning-v-2/lightning-v-2-tts

## AsyncAPI Specification

```yaml
asyncapi: 2.6.0
info:
  title: Lightning V2 TTS
  version: subpackage_lightningV2Tts.Lightning V2 TTS
  description: >-
    The Lightning v2 WebSocket API provides real-time text-to-speech streaming
    capabilities with high-quality voice synthesis. This API uses WebSocket to
    deliver audio chunks as they're generated, enabling low-latency audio
    playback without waiting for the entire audio file to process. Perfect for
    interactive applications, voice assistants, and real-time communication
    systems that require immediate audio feedback. For an end-to-end example of
    how to use the Lightning v2 WebSocket API, check out [Text to Speech (WS)
    Example](https://github.com/smallest-inc/waves-examples/tree/main/lightning_v2/ws_streaming)
channels:
  /waves/v1/lightning-v2/get_speech/stream:
    description: >-
      The Lightning v2 WebSocket API provides real-time text-to-speech streaming
      capabilities with high-quality voice synthesis. This API uses WebSocket to
      deliver audio chunks as they're generated, enabling low-latency audio
      playback without waiting for the entire audio file to process. Perfect for
      interactive applications, voice assistants, and real-time communication
      systems that require immediate audio feedback. For an end-to-end example
      of how to use the Lightning v2 WebSocket API, check out [Text to Speech
      (WS)
      Example](https://github.com/smallest-inc/waves-examples/tree/main/lightning_v2/ws_streaming)
    bindings:
      ws:
        headers:
          type: object
          properties:
            Authorization:
              type: string
    publish:
      operationId: lightning-v-2-tts-publish
      summary: LightningV2TtsResponse
      description: Receive audio data chunks and completion status from the server.
      message:
        name: LightningV2TtsResponse
        title: LightningV2TtsResponse
        description: Receive audio data chunks and completion status from the server.
        payload:
          $ref: >-
            #/components/schemas/lightningV2Stream_lightningV2TtsResponse.message
    subscribe:
      operationId: lightning-v-2-tts-subscribe
      summary: LightningV2TtsRequest
      description: >-
        Send a JSON message with voice_id, text, and optional parameters to
        generate speech audio.
      message:
        name: LightningV2TtsRequest
        title: LightningV2TtsRequest
        description: >-
          Send a JSON message with voice_id, text, and optional parameters to
          generate speech audio.
        payload:
          $ref: '#/components/schemas/lightningV2Stream_lightningV2TtsRequest.message'
servers:
  Production:
    url: wss://api.smallest.ai/
    protocol: wss
components:
  schemas:
    ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageStatus:
      type: string
      enum:
        - chunk
        - complete
      description: >-
        Status of the TTS request, `chunk` indicates incoming audio chunk,
        `complete` indicates completion.
      title: ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageStatus
    ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageData:
      type: object
      properties:
        audio:
          type: string
          description: Base64-encoded audio chunk
      title: ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageData
    lightningV2Stream_lightningV2TtsResponse.message:
      type: object
      properties:
        request_id:
          type: string
          description: Unique identifier for the TTS request
        status:
          $ref: >-
            #/components/schemas/ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageStatus
          description: >-
            Status of the TTS request, `chunk` indicates incoming audio chunk,
            `complete` indicates completion.
        data:
          $ref: >-
            #/components/schemas/ChannelsLightningV2StreamMessagesLightningV2TtsResponseMessageData
      title: lightningV2Stream_lightningV2TtsResponse.message
    lightningV2Stream_lightningV2TtsRequest.message:
      type: object
      properties:
        voice_id:
          type: string
          description: The ID of the voice to use
        text:
          type: string
          description: The text to convert to speech
        max_buffer_flush_ms:
          type: integer
          default: 0
          description: >-
            The maximum time (in ms) to wait for more input before generating
            output. It flushes when either this time is reached or enough input
            is received for optimal output—whichever comes first. This is useful
            for input streams. Deafults to 0
        continue:
          type: boolean
          default: false
          description: >-
            This setting controls whether the system should buffer and wait for
            more input after receiving the current one. If not set, it assumes
            no more input is coming.
        flush:
          type: boolean
          default: false
          description: >-
            This setting controls whether the system should flush the current
            buffer.
        complete_backoff_ms:
          type: number
          format: double
          default: 4000
          description: >-
            The time in ms to wait after the last chunk is sent before sending
            the complete response. Default is 4000ms. Maximum is 10000ms.
        language:
          type: string
          default: en
          description: >-
            The language code, available options: `en`, `hi`, `mr`, `kn`, `ta`,
            `bn`, `gu`, `de`, `fr`, `es`, `it`, `pl`, `nl`, `ru`, `ar`, `he`
        sample_rate:
          type: integer
          default: 24000
          description: 'Audio sample rate in Hz. Supported values: 8000, 16000, 24000, 44100'
        speed:
          type: number
          format: double
          default: 1
          description: Speaking speed multiplier
        consistency:
          type: number
          format: double
          default: 0.5
          description: Voice consistency parameter
        enhancement:
          type: integer
          default: 1
          description: Audio enhancement level
        similarity:
          type: number
          format: double
          default: 0
          description: Voice similarity parameter
      required:
        - voice_id
        - text
      title: lightningV2Stream_lightningV2TtsRequest.message

```
