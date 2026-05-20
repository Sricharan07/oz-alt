> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Agent WebSocket

GET /atoms/v1/agent/connect

A bidirectional session with an Atoms agent. Open the connection with
your API key and an `agent_id`; the server creates a session, bridges
audio and transcripts to the STT/LLM/TTS pipeline, and streams events
back until the client closes or the server ends the session.

Post-call, the full conversation (transcript + recording) is available
at `GET /atoms/v1/conversation/{callId}` using the `call_id` from
`session.created`.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/realtime-agent/realtime-agent

## AsyncAPI Specification

```yaml
asyncapi: 2.6.0
info:
  title: Realtime Agent
  version: subpackage_realtimeAgent.Realtime Agent
  description: |
    A bidirectional session with an Atoms agent. Open the connection with
    your API key and an `agent_id`; the server creates a session, bridges
    audio and transcripts to the STT/LLM/TTS pipeline, and streams events
    back until the client closes or the server ends the session.

    Post-call, the full conversation (transcript + recording) is available
    at `GET /atoms/v1/conversation/{callId}` using the `call_id` from
    `session.created`.
channels:
  /atoms/v1/agent/connect:
    description: |
      A bidirectional session with an Atoms agent. Open the connection with
      your API key and an `agent_id`; the server creates a session, bridges
      audio and transcripts to the STT/LLM/TTS pipeline, and streams events
      back until the client closes or the server ends the session.

      Post-call, the full conversation (transcript + recording) is available
      at `GET /atoms/v1/conversation/{callId}` using the `call_id` from
      `session.created`.
    publish:
      operationId: realtime-agent-publish
      summary: Server messages
      message:
        oneOf:
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-0-receiveSessionCreated
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-1-receiveSessionClosed
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-2-receiveOutputAudioDelta
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-3-receiveTranscript
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-4-receiveAgentStartTalking
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-5-receiveAgentStopTalking
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-6-receiveInterruption
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-server-7-receiveError
    subscribe:
      operationId: realtime-agent-subscribe
      summary: Client messages
      message:
        oneOf:
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-client-0-sendInputAudioAppend
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-client-1-sendInputAudioCommit
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-client-2-sendInputText
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-client-3-sendSessionUpdate
          - $ref: >-
              #/components/messages/subpackage_realtimeAgent.Realtime
              Agent-client-4-sendSessionClose
servers:
  Production server:
    url: wss://api.smallest.ai/
    protocol: wss
    x-default: true
components:
  messages:
    subpackage_realtimeAgent.Realtime Agent-server-0-receiveSessionCreated:
      name: receiveSessionCreated
      title: receiveSessionCreated
      payload:
        $ref: '#/components/schemas/agentSession_sessionCreated'
    subpackage_realtimeAgent.Realtime Agent-server-1-receiveSessionClosed:
      name: receiveSessionClosed
      title: receiveSessionClosed
      payload:
        $ref: '#/components/schemas/agentSession_sessionClosed'
    subpackage_realtimeAgent.Realtime Agent-server-2-receiveOutputAudioDelta:
      name: receiveOutputAudioDelta
      title: receiveOutputAudioDelta
      payload:
        $ref: '#/components/schemas/agentSession_outputAudioDelta'
    subpackage_realtimeAgent.Realtime Agent-server-3-receiveTranscript:
      name: receiveTranscript
      title: receiveTranscript
      payload:
        $ref: '#/components/schemas/agentSession_transcript'
    subpackage_realtimeAgent.Realtime Agent-server-4-receiveAgentStartTalking:
      name: receiveAgentStartTalking
      title: receiveAgentStartTalking
      payload:
        $ref: '#/components/schemas/agentSession_agentStartTalking'
    subpackage_realtimeAgent.Realtime Agent-server-5-receiveAgentStopTalking:
      name: receiveAgentStopTalking
      title: receiveAgentStopTalking
      payload:
        $ref: '#/components/schemas/agentSession_agentStopTalking'
    subpackage_realtimeAgent.Realtime Agent-server-6-receiveInterruption:
      name: receiveInterruption
      title: receiveInterruption
      payload:
        $ref: '#/components/schemas/agentSession_interruption'
    subpackage_realtimeAgent.Realtime Agent-server-7-receiveError:
      name: receiveError
      title: receiveError
      payload:
        $ref: '#/components/schemas/agentSession_error'
    subpackage_realtimeAgent.Realtime Agent-client-0-sendInputAudioAppend:
      name: sendInputAudioAppend
      title: sendInputAudioAppend
      payload:
        $ref: '#/components/schemas/agentSession_inputAudioAppend'
    subpackage_realtimeAgent.Realtime Agent-client-1-sendInputAudioCommit:
      name: sendInputAudioCommit
      title: sendInputAudioCommit
      payload:
        $ref: '#/components/schemas/agentSession_inputAudioCommit'
    subpackage_realtimeAgent.Realtime Agent-client-2-sendInputText:
      name: sendInputText
      title: sendInputText
      payload:
        $ref: '#/components/schemas/agentSession_inputTextSend'
    subpackage_realtimeAgent.Realtime Agent-client-3-sendSessionUpdate:
      name: sendSessionUpdate
      title: sendSessionUpdate
      payload:
        $ref: '#/components/schemas/agentSession_sessionUpdate'
    subpackage_realtimeAgent.Realtime Agent-client-4-sendSessionClose:
      name: sendSessionClose
      title: sendSessionClose
      payload:
        $ref: '#/components/schemas/agentSession_sessionClose'
  schemas:
    agentSession_sessionCreated:
      type: object
      properties:
        type:
          type: string
          enum:
            - session.created
        session_id:
          type: string
          description: Unique identifier for this session.
        call_id:
          type: string
          description: Call-log identifier; matches the `call_id` in conversation logs.
        sample_rate:
          type: integer
          description: Negotiated audio sample rate in Hz for both input and output audio.
        channels:
          type: integer
          description: Number of audio channels (typically 1).
      required:
        - type
        - session_id
        - call_id
        - sample_rate
        - channels
      title: agentSession_sessionCreated
    agentSession_sessionClosed:
      type: object
      properties:
        type:
          type: string
          enum:
            - session.closed
        reason:
          type: string
          description: |
            Why the session ended. Common values: `client_requested` (client
            sent `session.close`), `websocket_closed` (socket dropped),
            `server_error`, `timeout`, or a specific error tag.
      required:
        - type
        - reason
      title: agentSession_sessionClosed
    agentSession_outputAudioDelta:
      type: object
      properties:
        type:
          type: string
          enum:
            - output_audio.delta
        audio:
          type: string
          description: Base64-encoded raw audio chunk.
      required:
        - type
        - audio
      title: agentSession_outputAudioDelta
    ChannelsAgentSessionMessagesTranscriptRole:
      type: string
      enum:
        - user
        - agent
      description: Whose utterance this transcript is for.
      title: ChannelsAgentSessionMessagesTranscriptRole
    agentSession_transcript:
      type: object
      properties:
        type:
          type: string
          enum:
            - transcript
        role:
          $ref: '#/components/schemas/ChannelsAgentSessionMessagesTranscriptRole'
          description: Whose utterance this transcript is for.
        text:
          type: string
          description: The transcribed (or agent-generated) text.
      required:
        - type
        - role
        - text
      title: agentSession_transcript
    agentSession_agentStartTalking:
      type: object
      properties:
        type:
          type: string
          enum:
            - agent_start_talking
        timestamp:
          type: string
          format: date-time
          description: Server-side timestamp of when the agent turn started.
      required:
        - type
      title: agentSession_agentStartTalking
    agentSession_agentStopTalking:
      type: object
      properties:
        type:
          type: string
          enum:
            - agent_stop_talking
        timestamp:
          type: string
          format: date-time
          description: Server-side timestamp of when the agent turn ended.
      required:
        - type
      title: agentSession_agentStopTalking
    agentSession_interruption:
      type: object
      properties:
        type:
          type: string
          enum:
            - interruption
      required:
        - type
      title: agentSession_interruption
    agentSession_error:
      type: object
      properties:
        type:
          type: string
          enum:
            - error
        code:
          type: string
          description: |
            Machine-readable error code. Common values: `invalid_event`,
            `no_session`, `internal_error`, `voice_clone_timeout`,
            HTTP status codes like `401`, `503`.
        message:
          type: string
          description: Human-readable error message.
      required:
        - type
        - code
        - message
      title: agentSession_error
    agentSession_inputAudioAppend:
      type: object
      properties:
        type:
          type: string
          enum:
            - input_audio_buffer.append
        audio:
          type: string
          description: |
            Base64-encoded raw audio chunk. Format negotiated via the
            `sample_rate` query param at connection time and returned in
            `session.created`. Send chunks continuously while the user
            speaks — the server handles VAD and turn boundaries.
      required:
        - type
        - audio
      title: agentSession_inputAudioAppend
    agentSession_inputAudioCommit:
      type: object
      properties:
        type:
          type: string
          enum:
            - input_audio_buffer.commit
      required:
        - type
      title: agentSession_inputAudioCommit
    agentSession_inputTextSend:
      type: object
      properties:
        type:
          type: string
          enum:
            - input_text.send
        text:
          type: string
          description: User message text.
      required:
        - type
        - text
      title: agentSession_inputTextSend
    agentSession_sessionUpdate:
      type: object
      properties:
        type:
          type: string
          enum:
            - session.update
      required:
        - type
      title: agentSession_sessionUpdate
    agentSession_sessionClose:
      type: object
      properties:
        type:
          type: string
          enum:
            - session.close
      required:
        - type
      title: agentSession_sessionClose

```
